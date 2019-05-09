# meeup-demo
This is an example of data ingestion into Elasticsearch with the use of open API. Because this example utilizes the Meetup API, you need to register Meetup and get API KEY beforehand.

## Meetup API
See [here.](https://www.meetup.com/meetup_api/)

## Pre-Requisites
The python script of this example runs on Linux or Mac with Python 3, and also requires Elastic Stack environment to ingest the data.
1. Execution environment
  - Python 3.5 or later
  - Ensure pip3 is installed  
2. Elastic Stack
  - Elasticsearch cluster (7.0 or later)
  - Logstash (7.0 or later)

The easiest way to run the script is installing it and Logstash into same machine. See the following instructions for [installations of Elasticsearch and Logstash.](https://www.elastic.co/guide/en/elastic-stack-get-started/current/get-started-elastic-stack.html)


## Setup
1. Create user and group
First create user and group for this deployment.
```
$ sudo adduser meetup
$ sudo gpasswd -a meetup sudo
```
2. Clone repo
```
$ cd ~meetup
$ git clone https://github.com/yukshimizu/meetup-demo
```
3. Install dependencies
```
$ cd meetup-demo
$ pip3 install -f requirements.txt
```
4. Configure Logstash
Assuming that Logstash has been already installed on same machine, change logstash.yml file in order to enable Logstash management and monitoring features.
```
# X-Pack Monitoring
xpack.monitoring.enabled: true
xpack.monitoring.elasticsearch.username: elastic
xpack.monitoring.elasticsearch.password: changeme
xpack.monitoring.elasticsearch.hosts:["URL of elasticsearch cluster"]
# X-Pack Management
xpack.management.enabled: true
xpack.management.pipeline.id:["meetup"]
xpack.management.elasticsearch.username: elastic
xpack.management.elasticsearch.password: changeme
xpack.manegement.elasticsearch.hosts:["URL of elasticsearch cluster"]
```
5. Run Logstash
```
$ sudo systemctl start logstash.service
```
After Logstash service starts up, you need to create Logstash pipeline named "meetup" through Kibana dashboard. You can copy and paste the content of **meetup.conf** file.
Or, if you want to run Logstash from the command line:
```
$ bin/logstash -f meetup.conf
```
6. Configure script
Change API_KEY and LOGSTASH_URL environment variables in **capture_meetup.sh**.
```
# set Meetup API_KEY
export API_KEY="put here Meetup API key"
# set LOGSTASH_URL
export LOGSTASH_URL="http://0.0.0.0:8080/"
```
And, you can configure target countries as array in the script.
```
# list the target country code (ISO 3166-1 alpha-2)
countries=(
  "JP"
  "SG"
  "AU"
  "NZ"
  "IN"
  "HK"
  "KR"
  "CN"
  "MY"
  "TW"
  "US"
  "GB"
)
```
7. Run script
The script will take over a few hours to complete when running against the country which has a large amount of data such as US, GB, AU, JP, etc. Please take into account the target countries and execution time.
```
$ nohup ~meetup/meetup-demo/capture_meetup.sh >/dev/null 2>&1 &
```

## Configure Kibana for index
1. Access Kibana in a web browser
2. Login with the default credentials: username: elastic and password: changeme
3. Connect Kibana to the indices in Elasticsearch
Click the Management tab >> Index Patterns tab >> Create index pattern.
  - Specify **meetup-event** as the index pattern name, using the **updated_time** field as the Time-field name, and click Create index pattern.
  - Specify **meetup-group** as the index pattern name, using the **created_time** field as the Time-field name, and click Create index pattern.
  - Specify **meetup-topic** as the index pattern name, using the **updated** field as the Time-field name, and click Create index pattern.
  - Specify **meetup-category** as the index pattern name, using the **I don't want to use the Time Filter** as the Time-field name, and click Create index pattern.
4. Now you can configure any dashboards with any visualizations !
