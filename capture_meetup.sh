#!/usr/bin/env bash

# set Meetup API_KEY
export API_KEY="put here Meetup API key"
# set LOGSTASH_URL
export LOGSTASH_URL="http://0.0.0.0:8080/"

# list the target country code (ISO 3166-1 alpha-2)
countries=(
  "JP"
#  "SG"
#  "AU"
#  "NZ"
#  "IN"
#  "HK"
#  "KR"
#  "CN"
#  "MY"
#  "TW"
#  "US"
#  "GB"
)

python3 /home/meetup/meetup-demo/capture_meetup.py category
python3 /home//meetup/meetup-demo/capture_meetup.py topic

for country in "${countries[@]}"; do
  date
  echo "$country start!"
  python3 /home/meetup/meetup-demo/capture_meetup.py -c $country  group
  python3 /home/meetup/meetup-demo/capture_meetup.py -c $country  event
  sleep 5
done

date