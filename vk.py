import base64
import collections
import hashlib
import hmac
import urllib.parse

APP_ID = "7472129"

def extract_data(vk_secret, s):
    if s.startswith("?"):
        s = s[1:]

    params = dict(urllib.parse.parse_qsl(s, keep_blank_values=True))


    hash_code = hashlib.md5((APP_ID + params['uid'] + vk_secret).encode()).hexdigest()
    print(hash_code)
    if params["hash"] != hash_code:
        return None

    return params

if __name__ == "__main__":
    key = input("SECRET: ")
    query = input("QUERY: ")
    print(extract_data(key, query))
