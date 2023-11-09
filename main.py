from prototype.utils import elgamal
import sys

key_pair = elgamal.generate_keys(256)

msg = 'a' * 3072 * 100
print(sys.getsizeof(msg))

# 60秒
cipher = elgamal.encrypt(key_pair['publicKey'], msg)
# plaintext = elgamal.decrypt(key_pair['privateKey'], cipher)