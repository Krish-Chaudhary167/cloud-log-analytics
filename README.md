# Cloud-Based Log Analytics Pipeline

A cloud computing system that collects, stores, processes and analyzes application and user-activity logs. A RESTful service on **AWS EC2** receives mock log data and stores it in **AWS S3**. The logs are then processed with **Hadoop HDFS and MapReduce** to compute error trends, daily active users, request counts and possible security anomalies. The aggregated results are stored in **MongoDB (NoSQL)** and shown on a live analytics dashboard.


## Dashboard

The dashboard after processing the first 5,000 log lines:

Dashboard with 5,000 requests
<img width="1917" height="1022" alt="image" src="https://github.com/user-attachments/assets/563121f2-b327-4a31-9e89-bde0452a6ba7" />


After sending 5,000 fresh logs through the REST API and re-running the pipeline, the totals double to 10,000 with no manual changes:

Dashboard with 10,000 requests
<img width="1862" height="976" alt="image" src="https://github.com/user-attachments/assets/4c28df67-156e-4832-8c0f-cbeac300bd9f" />


<!--
More screenshots you can add to the docs/ folder and uncomment:
![S3 bucket](docs/01-s3-bucket.png)
![Hadoop daemons (jps)](docs/02-jps-hadoop.png)
![MapReduce job](docs/04-mapreduce-job.png)
![MongoDB collections](docs/05-mongodb-collections.png)
-->

## Architecture

<img width="2400" height="1110" alt="image" src="https://github.com/user-attachments/assets/296625e2-303e-467e-ba47-1420f2d0bb3e" />


| Stage | Component | What it does |
|---|---|---|
| 1 | Mock log generator | Creates realistic web-traffic logs, including planted error spikes and brute-force attackers |
| 2 | RESTful API (Flask on EC2) | `POST /logs` receives log batches. `GET /analytics` returns results as JSON. `GET /` serves the dashboard |
| 3 | AWS S3 | Stores raw log batches, organized by date (`logs/YYYY-MM-DD/batch-*.log`) |
| 4 | HDFS + MapReduce | Distributed storage and processing of the logs using Hadoop Streaming with Python |
| 5 | MongoDB Atlas | Stores the aggregated results, one collection per metric |
| 6 | Analytics dashboard | Single web page with KPI cards and charts, served by the Flask API |

## Technologies

| Component | Technology | Purpose |
|---|---|---|
| Cloud compute | AWS EC2 (Ubuntu 24.04, c7i-flex.large) | Hosts the REST API and the Hadoop processing |
| Data collection | AWS S3 | Stores incoming log files |
| Big data | Hadoop 3.3.6 (HDFS, YARN, MapReduce), pseudo-distributed mode | Distributed storage and log processing |
| Database | MongoDB Atlas (M0 free tier) | Stores aggregated analytics |
| API | Python, Flask, boto3, pymongo | Receives logs and exposes analytics |
| Frontend | HTML, Chart.js | Charts for the analytics dashboard |
| Security | IAM user and IAM role, security groups, `.env` for secrets | Least-privilege access to AWS services |

## Log format

One line per request, comma-separated:

```
timestamp,user_id,ip,endpoint,method,status,response_time_ms
2026-11-25 14:32:10,user12,192.168.1.34,/cart,GET,200,123
```

The generator plants patterns that the analytics must find:

- 50 users and 8 endpoints over 7 days
- An error spike between 2 PM and 4 PM
- 3 attacker IPs repeatedly failing `/login` with status 401

## MapReduce jobs

Each job is a Python mapper and reducer run with Hadoop Streaming.

| Job | Mapper emits | Reducer produces | MongoDB collection |
|---|---|---|---|
| `requests_per_endpoint` | `endpoint -> 1` | request count per endpoint | `requests_per_endpoint` |
| `errors_per_hour` | `hour -> (1, is_error)` | total requests and errors per hour | `errors_per_hour` |
| `daily_active_users` | `date -> user_id` | number of unique users per day | `daily_active_users` |
| `anomalies` | `ip -> 1` for each 401 response | IPs with 20 or more failed requests | `anomalies` |

## Results

From the second run (10,000 log lines):

| Metric | Value |
|---|---|
| Total requests | 10,000 |
| Total errors (4xx/5xx) | 1,020 (10.2%) |
| Peak daily active users | 50 |
| Suspicious IPs detected | 3 |

The error-rate-by-hour chart shows the planted 2 to 4 PM spike, and the anomaly table lists exactly the 3 attacker IPs.

## Project structure

```
cloud-log-analytics/
├── api/
│   └── app.py                  Flask REST API (/logs, /analytics, dashboard)
├── generator/
│   ├── generate_logs.py        mock log generator
│   └── send_logs.py            sends generated logs to the API
├── mapreduce/
│   ├── requests_per_endpoint/  mapper.py, reducer.py
│   ├── errors_per_hour/        mapper.py, reducer.py
│   ├── daily_active_users/     mapper.py, reducer.py
│   ├── anomalies/              mapper.py, reducer.py
│   └── local_test.py           runs map -> sort -> reduce locally for testing
├── loader/
│   ├── loader.py               HDFS output -> MongoDB
│   └── test_connection.py      checks the MongoDB connection
├── dashboard/
│   └── index.html              analytics dashboard (Chart.js)
├── scripts/
│   └── run_pipeline.sh         runs the whole pipeline with one command
├── docs/                       screenshots
├── requirements.txt
└── README.md
```

## Setup and run

### 1. Local setup

```bash
git clone https://github.com/Krish-Chaudhary167/cloud-log-analytics.git
cd cloud-log-analytics
python -m venv venv
# Windows: venv\Scripts\activate    Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (it is listed in `.gitignore` and must never be committed):

```
AWS_ACCESS_KEY_ID=your_key           # local use only; on EC2 use an IAM role
AWS_SECRET_ACCESS_KEY=your_secret    # local use only
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET=your-bucket-name
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGO_DB=log_analytics
```

### 2. Test the MapReduce logic locally

```bash
python generator/generate_logs.py --count 5000 --days 7
python mapreduce/local_test.py requests_per_endpoint
python mapreduce/local_test.py anomalies
```

### 3. Deploy on AWS

1. Create an S3 bucket.
2. Launch an Ubuntu EC2 instance (4 GB RAM or more) with an IAM role that allows S3 access. Open port 5000 in the security group only to your own IP.
3. Install Java 11 and Hadoop 3.3.6 and configure pseudo-distributed mode. Then run `hdfs namenode -format`, `start-dfs.sh` and `start-yarn.sh`.
4. Create a MongoDB Atlas free cluster and allow the EC2 server's IP under Network Access.
5. Install the AWS CLI on the server and clone this repository.

### 4. Run the pipeline

On the EC2 server, start the API:

```bash
source ~/venv/bin/activate
nohup python api/app.py > api.log 2>&1 &
```

From any machine, send logs to the API:

```bash
python generator/send_logs.py http://<EC2_PUBLIC_IP>:5000
```

On the EC2 server, process everything with one command:

```bash
./scripts/run_pipeline.sh
```

The script syncs logs from S3, loads them into HDFS, runs the 4 MapReduce jobs and loads the results into MongoDB. Then open `http://<EC2_PUBLIC_IP>:5000` to see the dashboard.

## Hadoop configuration notes

| Setting | Value | Reason |
|---|---|---|
| `dfs.replication` | 1 | Single node. A real cluster would use 3 |
| `yarn.nodemanager.resource.memory-mb` | 3072 | Fits within the 4 GB instance |
| `mapreduce.map.memory.mb` / `mapreduce.reduce.memory.mb` | 512 | Small containers for a small machine |
| `yarn.nodemanager.vmem-check-enabled` | false | Avoids healthy tasks being killed by the virtual-memory check |

## Security

- Secrets (AWS keys, MongoDB connection string, `.pem` key) are kept in `.env` or outside the repository and are excluded by `.gitignore`.
- The EC2 server reads S3 through an IAM role, so no AWS keys are stored on it.
- The EC2 security group allows SSH and port 5000 only from the developer's IP.
- MongoDB Atlas accepts connections only from the allowed IP list.

## Author

Krish Chaudhary,
Kudrat Aggarwal
