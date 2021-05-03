import requests

headers = {'Authorization': 'Bearer ' + 'd43906d7756cf666c38faf6ee0f4935bdfdc0086'}

response = requests.get(
    url="https://www.strava.com/api/v3/athlete",
    headers=headers
)

print(response)
data = {
    'client_id': 64981,
    'client_secret': '4d34725e9687ff046930a3f6db5aadbaa9042b6b',
    'code': '',
    'grant_type': 'authorization_code'
}
response = requests.post(
    url="https://www.strava.com/api/v3/oauth/token",
    data=data

)
