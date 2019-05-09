import argparse
import datetime
import dateutil.parser
import json
import os
import requests
from time import sleep

API_KEY = os.getenv("API_KEY")
LOGSTASH_URL = os.getenv("LOGSTASH_URL")
CITIES_URL = "https://api.meetup.com/2/cities"
EVENTS_URL = "https://api.meetup.com/2/open_events"
GROUPS_URL = "https://api.meetup.com/2/groups"
CATEGORIES_URL = "https://api.meetup.com/2/categories"
VENUES_URL = "https://api.meetup.com/2/open_venues"
TOPICS_URL = "https://api.meetup.com/topics"
MAX_RETRY = 3
MAX_PAGE = 1000
CITY_MAX_PAGE = 2000
PAGE_DEFAULT = 200
# Some sleep period is required so that API_CALLs are not disconnected by Meetup
SLEEP = 1
STATE_DEFAULT = "nowhere"


def post_logstash(payload):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    requests.post(LOGSTASH_URL, data=payload, headers=headers)


def get_cities(country_code, page=200):
    # Get Cities via API
    payload = {"Key": API_KEY, "page": page, "country": country_code}
    json_response = {}
    try:
        response = requests.get(CITIES_URL, payload, timeout=30)
        json_response = response.json()
    except TimeoutError as e:
        print("timeout:", str(e))
    except Exception as e:
        print("exception:", str(e))

    if "results" in json_response:
        cities = json_response["results"]
    else:
        cities = None

    # Iterate if there is next page
    sleep(SLEEP)
    p = page
    r = 1
    while ("meta" in json_response) and (json_response["meta"]["next"] != "") \
            and (p <= CITY_MAX_PAGE) and (r <= MAX_RETRY):
        try:
            response = requests.get(json_response["meta"]["next"], timeout=30)
            json_response = response.json()
        except TimeoutError as e:
            print("timeout:", str(e), "retry:", r)
            r += 1
            continue
        except Exception as e:
            print("exception:", str(e))
            r += 1
            continue

        if "results" in json_response:
            cities += json_response["results"]
            p = p + page

        sleep(SLEEP)

    return cities


def get_events(country_code, city, state=STATE_DEFAULT):
    # Get Open Events via API
    if state == STATE_DEFAULT:
        payload = {"key": API_KEY, "city": city, "country": country_code}
    else:
        payload = {"key": API_KEY, "city": city, "country": country_code, "state": state}
    json_response = {}
    try:
        response = requests.get(EVENTS_URL, payload, timeout=30)
        json_response = response.json()
    except TimeoutError as e:
        print("timeout:", str(e))
    except Exception as e:
        print("exception:", str(e))

    if "results" in json_response:
        events = json_response["results"]
        post_logstash(edit_event(events))

    # Iterate if there is next page
    sleep(SLEEP)
    p = PAGE_DEFAULT
    r = 1
    while ("meta" in json_response) and (json_response["meta"]["next"] != "") and (p <= MAX_PAGE) and (r <= MAX_RETRY):
        print(city, ":", p)
        try:
            response = requests.get(json_response["meta"]["next"], timeout=30)
            json_response = response.json()
        except TimeoutError as e:
            print("timeout:", str(e), "retry:", r)
            r += 1
            continue
        except Exception as e:
            print("exception:", str(e))
            r += 1
            continue

        if "results" in json_response:
            events = json_response["results"]
            post_logstash(edit_event(events))
            p += PAGE_DEFAULT

        sleep(SLEEP)


def edit_event(events):
    for event in events:
        our_event_id = "event_id_" + str(event["id"])
        start_time = event["time"]
        event["start_time"] = datetime.datetime.fromtimestamp(float(start_time / 1000)).isoformat()
        created_time = event["created"]
        event["created_time"] = datetime.datetime.fromtimestamp(float(created_time / 1000)).isoformat()
        updated_time = event["updated"]
        event["updated_time"] = datetime.datetime.fromtimestamp(float(updated_time / 1000)).isoformat()
        group_created_time = event["group"]["created"]
        event["group"]["created_time"] = datetime.datetime.fromtimestamp(float(group_created_time / 1000)).isoformat()
        if "duration" in event:
            duration_min = event["duration"]
            event["duration_min"] = duration_min / 1000 / 60
        event["document_id"] = our_event_id
        event["data_type"] = "event"
        if "venue" in event:
            venue_country = str(event["venue"]["country"]).upper()
            event["venue"]["country"] = venue_country

    return json.dumps(events)


def get_groups(country_code, city, state=STATE_DEFAULT):
    # Get Groups via API
    if state == STATE_DEFAULT:
        payload = {"key": API_KEY, "city": city, "country": country_code}
    else:
        payload = {"key": API_KEY, "city": city, "country": country_code, "state": state}
    json_response = {}
    try:
        response = requests.get(GROUPS_URL, payload, timeout=30)
        json_response = response.json()
    except TimeoutError as e:
        print("timeout:", str(e))
    except Exception as e:
        print("exception:", str(e))

    if "results" in json_response:
        groups = json_response["results"]
        post_logstash(edit_group(groups))

    # Iterate if there is next page
    sleep(SLEEP)
    p = PAGE_DEFAULT
    r = 1
    while ("meta" in json_response) and (json_response["meta"]["next"] != "") and (p <= MAX_PAGE) and (r <= MAX_RETRY):
        print(city, ":", p)
        try:
            response = requests.get(json_response["meta"]["next"], timeout=30)
            json_response = response.json()
        except TimeoutError as e:
            print("timeout:", str(e), "retry:", r)
            r += 1
            continue
        except Exception as e:
            print("exception:", str(e))
            r += 1
            continue

        if "results" in json_response:
            groups = json_response["results"]
            post_logstash(edit_group(groups))
            p += PAGE_DEFAULT

        sleep(SLEEP)


def edit_group(groups):
    for group in groups:
        our_group_id = "group_id_" + str(group["id"])
        created_time = group["created"]
        group["created_time"] = datetime.datetime.fromtimestamp(float(created_time/1000)).isoformat()
        group["document_id"] = our_group_id
        group["data_type"] = "group"
        group_country = str(group["country"]).upper()
        group["country"] = group_country

    return json.dumps(groups)


def get_categories():
    # Get Categories via API
    payload = {"key": API_KEY}
    json_response = {}
    try:
        response = requests.get(CATEGORIES_URL, payload, timeout=30)
        json_response = response.json()
    except TimeoutError as e:
        print("timeout:", str(e))
    except Exception as e:
        print("exception:", str(e))

    if "results" in json_response:
        categories = json_response["results"]
        post_logstash(edit_category(categories))

    # Iterate if there is next page
    sleep(SLEEP)
    p = PAGE_DEFAULT
    r = 1
    while ("meta" in json_response) and (json_response["meta"]["next"] != "") and (p <= MAX_PAGE) and (r <= MAX_RETRY):
        print(p)
        try:
            response = requests.get(json_response["meta"]["next"], timeout=30)
            json_response = response.json()
        except TimeoutError as e:
            print("timeout:", str(e), "retry:", r)
            r += 1
            continue
        except Exception as e:
            print("exception:", str(e))
            r += 1
            continue

        if "results" in json_response:
            categories = json_response["results"]
            post_logstash(edit_category(categories))
            p += PAGE_DEFAULT

        sleep(SLEEP)


def edit_category(categories):
    for category in categories:
        our_category_id = "category_id_" + str(category["id"])
        category["document_id"] = our_category_id
        category["data_type"] = "category"

    return json.dumps(categories)


def get_venues(country_code, city, state=STATE_DEFAULT):
    # Get Venues via API
    if state == STATE_DEFAULT:
        payload = {"key": API_KEY, "city": city, "country": country_code}
    else:
        payload = {"key": API_KEY, "city": city, "country": country_code, "state": state}
    json_response = {}
    try:
        response = requests.get(VENUES_URL, payload, timeout=30)
        json_response = response.json()
    except TimeoutError as e:
        print("timeout:", str(e))
    except Exception as e:
        print("exception:", str(e))

    if "results" in json_response:
        venues = json_response["results"]
        post_logstash(edit_venue(venues))

    # Iterate if there is next page
    sleep(SLEEP)
    p = PAGE_DEFAULT
    r = 1
    while ("meta" in json_response) and (json_response["meta"]["next"] != "") and (p <= MAX_PAGE) and (r <= MAX_RETRY):
        print(p)
        try:
            response = requests.get(json_response["meta"]["next"], timeout=30)
            json_response = response.json()
        except TimeoutError as e:
            print("timeout:", str(e), "retry:", r)
            r += 1
            continue
        except Exception as e:
            print("exception:", str(e))
            r += 1
            continue

        if "results" in json_response:
            venues = json_response["results"]
            post_logstash(edit_venue(venues))
            p += PAGE_DEFAULT

        sleep(SLEEP)


def edit_venue(venues):
    for venue in venues:
        our_venue_id = "venue_id_" + str(venue["id"])
        venue["document_id"] = our_venue_id
        venue["data_type"] = "venue"
        venue_country = str(venue["country"]).upper()
        venue["country"] = venue_country

    return json.dumps(venues)


def get_topics():
    # Get Topics via API
    payload = {"key": API_KEY}
    json_response = {}
    try:
        response = requests.get(TOPICS_URL, payload, timeout=30)
        json_response = response.json()
    except TimeoutError as e:
        print("timeout:", str(e))
    except Exception as e:
        print("exception:", str(e))

    if "results" in json_response:
        topics = json_response["results"]
        post_logstash(edit_topic(topics))

    # Iterate if there is next page
    sleep(SLEEP)
    p = PAGE_DEFAULT
    r = 1
    while ("meta" in json_response) and (json_response["meta"]["next"] != "") and (p <= MAX_PAGE) and (r <= MAX_RETRY):
        print(p)
        try:
            response = requests.get(json_response["meta"]["next"], timeout=30)
            json_response = response.json()
        except TimeoutError as e:
            print("timeout:", str(e), "retry:", r)
            r += 1
            continue
        except Exception as e:
            print("exception:", str(e))
            r += 1
            continue

        if "results" in json_response:
            topics = json_response["results"]
            post_logstash(edit_topic(topics))
            p += PAGE_DEFAULT

        sleep(SLEEP)


def edit_topic(topics):
    for topic in topics:
        our_topic_id = "topic_id_" + str(topic["id"])
        updated_time = topic["updated"]
        topic["updated"] = dateutil.parser.parse(updated_time).isoformat()
        topic["document_id"] = our_topic_id
        topic["data_type"] = "topic"

    return json.dumps(topics)


def main():
    parser = argparse.ArgumentParser(description="Capture Meetup")

    parser.add_argument(dest="function", metavar="function", choices={"event", "group", "venue", "category", "topic"},
                        action="store", help="execution function")
    parser.add_argument("-c", "--country", dest="country", metavar="country_code", action="store",
                        help="target country code")

    args = parser.parse_args()
    print("country code:", args.country)
    print("function:", args.function)
    print("API_KEY:", API_KEY)
    print("LOGSTASH_URL:", LOGSTASH_URL)
    return

    if args.function == "event":
        cities = get_cities(args.country, PAGE_DEFAULT)
        for city in cities:
            if "state" in city:
                get_events(args.country, city["city"], city["state"])
            else:
                get_events(args.country, city["city"])
    elif args.function == "group":
        cities = get_cities(args.country, PAGE_DEFAULT)
        for city in cities:
            if "state" in city:
                get_groups(args.country, city["city"], city["state"])
            else:
                get_groups(args.country, city["city"])
    elif args.function == "venue":
        cities = get_cities(args.country, PAGE_DEFAULT)
        for city in cities:
            if "state" in city:
                get_venues(args.country, city["city"], city["state"])
            else:
                get_venues(args.country, city["city"])
    elif args.function == "category":
        get_categories()
    elif args.function == "topic":
        get_topics()


if __name__ == "__main__":
    main()
