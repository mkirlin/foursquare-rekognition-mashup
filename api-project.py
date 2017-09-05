import io
import pdb
import ssl
import boto3
import random
import requests
import foursquare
import webbrowser
from urllib.request import urlopen

REKOGNITION_CLIENT = boto3.client('rekognition')
S3_CLIENT = boto3.resource('s3')
ZIP_CODE_API_ACCESS_TOKEN = 'lsvpnxeuFWYdMy46WuxaZNw03jHxMqc8SIxfgLKVHI8uhdBdH8oHWUHZdpx0PJ9I'
FOURSQUARE_CLIENT = foursquare.Foursquare(client_id='VMJ1CNV3GJIPRLG5IQDIYKIIDVBKH0ZTKVGK4BPAYTXB0PMM', client_secret='D1OGVTTOLLXAUNUWOVGNKBBFY3LB53X0SX3MROSRQ4C4SOZU')
AWS_STORAGE_BUCKET_NAME = 'tc-coding-challenge'

def get_coordinates_from_zip_code(zip_code: str):
  zip_code_json_info = requests.get("https://www.zipcodeapi.com/rest/{access_token}/info.json/{zip_code}/degrees".format(
    access_token=ZIP_CODE_API_ACCESS_TOKEN,
    zip_code=zip_code)
  ).json()

  latitude = zip_code_json_info.get('lat')
  longitude = zip_code_json_info.get('lng')

  return (latitude, longitude)

def search_for_foursquare_venues(latitude: float, longitude: float):
  location_string = "{},{}".format(latitude, longitude)
  venues =  FOURSQUARE_CLIENT.venues.search(
    params={
      "ll": location_string,
      "radius": 1000,
      "limit": 100
    }
  )['venues']

  return venues

def get_venue_photos(venue_id: int):
  photos = FOURSQUARE_CLIENT.venues.photos(
    venue_id,
    params={'VENUE_ID': venue_id}
  )['photos']

  return photos

def scrape_photo_to_s3(photo_url: str):
  bucket = S3_CLIENT.Bucket(AWS_STORAGE_BUCKET_NAME)
  gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
  file_object = urlopen(photo_url, context=gcontext)
  fp = io.BytesIO(file_object.read())
  bucket.upload_fileobj(fp, photo_url)

def detect_faces_in_photos(s3_key_name: str):
  response = REKOGNITION_CLIENT.detect_faces(
    Image={
      'S3Object': {
        'Bucket': AWS_STORAGE_BUCKET_NAME,
        'Name': s3_key_name,
      }
    },
    Attributes=['ALL']
  )

  return response

def report_on_facial_recognition(photos: list):
  photos = [photo for photo in photos if len(photo['facial_recognition_analysis']['FaceDetails']) > 0]
  if photos:
    print("A series of photos with faces in them will appear as new tabs in your most recent browser window.")
    print("Here are the analyses of these photos, in left to right tab order.")
    for photo in photos:
      webbrowser.open(photo['full_url'], new=2)
      print_photo_report(photo)
  else:
    print("None of the photos in this set had recognizable faces in them.")

def get_conf_mod(confidence_value: float):
  if confidence_value >= 90:
    confidence_modifier = "almost certainly"
  elif confidence_value < 90 and confidence_value >= 66:
    confidence_modifier = "probably"
  else:
    confidence_modifier = "maybe"

  return confidence_modifier

def get_overall_confidence(confidence_value: float):
  if confidence_value >= 90:
    confidence_modifier = "very accurate"
  elif confidence_value < 90 and confidence_value >= 66:
    confidence_modifier = "somewhat accurate"
  else:
    confidence_modifier = "probably inaccurate"

  return confidence_modifier

def print_photo_report(photo: dict):
  face_details = photo['facial_recognition_analysis']['FaceDetails']

  print("----------------------------------------------------------")
  print(
    "This is a report for {photo_url}. Rekognition has detected {number_of_faces} face(s) in this photo. Here are the details about them".format(
      photo_url=photo["full_url"],
      number_of_faces=len(face_details),
    )
  )
  counter = 0
  for face in face_details:
    counter += 1
    overall_confidence = get_overall_confidence(face['Confidence'])
    gender = face['Gender']['Value'].lower()
    gender_confidence = round(face['Gender']['Confidence'])
    low_age = face['AgeRange']['Low']
    high_age = face['AgeRange']['High']
    smiling = 'smiling' if face['Smile']['Value'] else 'not smiling'
    smile_confidence = face['Smile']['Confidence']
    beard = face['Beard']['Value']
    beard_confidence = face['Beard']['Confidence']
    mustache = face['Mustache']['Value']
    mustache_confidence = face['Mustache']['Confidence']
    eyeglasses = face['Eyeglasses']['Value']
    eyeglasses_confidence = face['Eyeglasses']['Confidence']
    sunglasses = face['Sunglasses']['Value']
    sunglasses_confidence = face['Sunglasses']['Confidence']
    eyes_open = face['EyesOpen']['Value']
    eyes_open_confidence = face['EyesOpen']['Confidence']
    mouth_open = face['MouthOpen']['Value']
    mouth_open_confidence = face['MouthOpen']['Confidence']
    most_likely_emotion = face['Emotions'][0]['Type'].lower()
    most_likely_emotion_confidence = face['Emotions'][0]['Confidence']

    print(
      "Person {counter}. Overall, the facial recognition software rates this analysis as {overall_confidence}".format(
        counter=counter,
        overall_confidence=overall_confidence
      )
    )
    print(
      "Rekognition believes this person is {confidence_modifier} a {gender} between the ages of {low_age} and {high_age}.".format(
        confidence_modifier=get_conf_mod(gender_confidence),
        gender=gender,
        low_age=low_age,
        high_age=high_age,
      )
    )
    print(
      "This person is {confidence_modifier} {smiling}.".format(
        confidence_modifier=get_conf_mod(smile_confidence),
        smiling=smiling,
      )
    )
    if beard or mustache:
      print(
        "They {beard_confidence_modifier} have a beard, and they {mustache_confidence_modifier} have a mustache.".format(
          beard_confidence_modifier=get_conf_mod(beard_confidence),
          mustache_confidence_modifier=get_conf_mod(mustache_confidence),
        )
      )
    else:
      print(
        "They most likely do not have any facial hair."
      )
    if sunglasses or eyeglasses:
      print(
        "This person is {sunglasses_confidence_modifier} wearing sunglasses, and they are {eyeglasses_confidence_modifier} wearing eyeglasses.".format(
          sunglasses_confidence_modifier=get_conf_mod(sunglasses_confidence),
          eyeglasses_confidence_modifier=get_conf_mod(eyeglasses_confidence),
        )
      )
    else:
      print("This person is probably not wearing any eyewear.")
    if eyes_open:
      print(
        "Their eyes are {eyes_open_confidence_modifier} open.".format(
          eyes_open_confidence_modifier=get_conf_mod(eyes_open_confidence)
        )
      )
    else:
      print(
        "Their eyes are {eyes_open_confidence_modifier} closed.".format(
          eyes_open_confidence_modifier=get_conf_mod(eyes_open_confidence)
        )
      )
    if mouth_open:
      print(
        "Their mouth is {mouth_open_confidence_modifier} open.".format(
          mouth_open_confidence_modifier=get_conf_mod(mouth_open_confidence)
        )
      )
    else:
      print(
        "Their mouth is {mouth_open_confidence_modifier} closed.".format(
          mouth_open_confidence_modifier=get_conf_mod(mouth_open_confidence)
        )
      )
    print(
      "Finally, Rekognition believes this person is {emotion_confidence_modifier} {emotion}.".format(
        emotion_confidence_modifier=get_conf_mod(most_likely_emotion_confidence),
        emotion=most_likely_emotion,
      )
    )

# Actual User Input
user_zipcode = input("Enter a zipcode to scan a random event for faces: ")
lat, lng = get_coordinates_from_zip_code(user_zipcode)

# Test Values for 60605
# lat = 41.867574
# lng = -87.617277

if lat and lng:
  print("Grabbing nearby venues and their associated photos from Foursquare's API based on the zip code you entered.")
  nearby_venues = search_for_foursquare_venues(lat, lng)
  for venue in nearby_venues:
    photos = get_venue_photos(venue['id'])
    venue['photos'] = photos

  print("Picking a random venue that has associated photos.")
  venues_with_photos = [venue for venue in nearby_venues if venue['photos']['count'] > 0]
  random_venue = random.choice(venues_with_photos)
  photos = random_venue['photos']['items']

  print("Scraping photos to S3 and running facial recognition on them.")
  for photo in photos:
    full_url = "{prefix}original{suffix}".format(
      prefix=photo['prefix'],
      suffix=photo['suffix']
    )
    scrape_photo_to_s3(full_url)
    photo['full_url'] = full_url
    facial_recognition_analysis = detect_faces_in_photos(full_url)
    photo['facial_recognition_analysis'] = facial_recognition_analysis

  report_on_facial_recognition(photos)
else:
  print("Could not retrieve latitude and longitude for zip code as entered.")
