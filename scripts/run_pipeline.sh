#!/bin/bash
# Full pipeline: S3 -> HDFS -> MapReduce -> MongoDB
set -e

export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

PROJECT=$HOME/cloud-log-analytics
BUCKET=$(grep '^S3_BUCKET=' "$PROJECT/.env" | cut -d= -f2)
STREAMING_JAR=$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar
JOBS="requests_per_endpoint errors_per_hour daily_active_users anomalies"

echo "== 1/5 Checking that Hadoop is running =="
if ! jps | grep -q NameNode; then
  echo "Hadoop is not running. Start it with: start-dfs.sh && start-yarn.sh"
  exit 1
fi

echo "== 2/5 Downloading logs from S3 =="
mkdir -p "$HOME/logs"
aws s3 sync "s3://$BUCKET/logs" "$HOME/logs"

echo "== 3/5 Loading logs into HDFS =="
hdfs dfs -rm -r -f /input/logs /output
hdfs dfs -mkdir -p /input/logs
hdfs dfs -put "$HOME"/logs/*/*.log /input/logs/

echo "== 4/5 Running MapReduce jobs =="
for JOB in $JOBS; do
  echo "-- $JOB"
  (cd "$PROJECT/mapreduce/$JOB" && hadoop jar "$STREAMING_JAR" \
    -files mapper.py,reducer.py \
    -mapper "python3 mapper.py" \
    -reducer "python3 reducer.py" \
    -input /input/logs \
    -output "/output/$JOB")
done

echo "== 5/5 Loading results into MongoDB =="
"$HOME/venv/bin/python" "$PROJECT/loader/loader.py"

echo "Pipeline finished."
