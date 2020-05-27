import base64
import collections
import hashlib
import hmac
import urllib.parse


def extract_data(vk_secret, s):
    if s.startswith("?"):
        s = s[1:]

    params = dict(urllib.parse.parse_qsl(s, keep_blank_values=True))

    vk_params = collections.OrderedDict(sorted(
        (key, value)
        for key, value in params.items() if key.startswith("vk_")
    ))

    vk_params_enc = urllib.parse.urlencode(vk_params, doseq=True)

    hash_code = base64.b64encode(hmac.HMAC(
        vk_secret.encode(),
        vk_params_enc.encode(),
        hashlib.sha256,
    ).digest())

    decoded_hash_code = hash_code.decode()[:-1] \
        .replace("+", "-").replace("/", "_")

    if params["sign"] != decoded_hash_code:
        return None

    return params
