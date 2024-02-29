import requests

d = {
  "name": "John Doe",
  "age": 21,
  "courses": [
    {"courseName": "Mathematics", "grades": [88, 90, 94]},
    {"courseName": "Physics", "grades": [92, 85, 100]}
  ]
}

rc =requests.post(
    'https://demo02.scratchdb.com/data?api_key=demo&table=flatblog2&flatten=explode',
    json=d
)
print(rc)