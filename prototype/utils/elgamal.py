import json

from Crypto.Util.number import inverse as multiplicative_inverse
from Crypto.Math.Primality import generate_probable_safe_prime
from Crypto.Math.Numbers import Integer
from Crypto.Random.random import randrange
import random


# finds a primitive root for prime p
# this function was implemented from the algorithm described here:
# http://modular.math.washington.edu/edu/2007/spring/ent/ent-html/node31.html
def find_primitive_root(p):
    if p == 2:
        return 1
    # the prime divisors of p-1 are 2 and (p-1)/2 because
    # p = 2x + 1 where x is a prime
    p1 = 2
    p2 = (p - 1) // p1

    # test random g's until one is found that is a primitive root mod p
    while 1:
        g = random.randint(2, p - 1)
        # g is a primitive root if for all prime factors of p-1, p[i]
        # g^((p-1)/p[i]) (mod p) is not congruent to 1
        if not (pow(g, (p - 1) // p1, p) == 1):
            if not pow(g, (p - 1) // p2, p) == 1:
                return g


# computes the jacobi symbol of a, n
def jacobi(a, n):
    if a == 0:
        if n == 1:
            return 1
        else:
            return 0
    # property 1 of the jacobi symbol
    elif a == -1:
        if n % 2 == 0:
            return 1
        else:
            return -1
    # if a == 1, jacobi symbol is equal to 1
    elif a == 1:
        return 1
    # property 4 of the jacobi symbol
    elif a == 2:
        if n % 8 == 1 or n % 8 == 7:
            return 1
        elif n % 8 == 3 or n % 8 == 5:
            return -1
    # property of the jacobi symbol:
    # if a = b mod n, jacobi(a, n) = jacobi( b, n )
    elif a >= n:
        return jacobi(a % n, n)
    elif a % 2 == 0:
        return jacobi(2, n) * jacobi(a // 2, n)
    # law of quadratic reciprocity
    # if a is odd and a is coprime to n
    else:
        if a % 4 == 3 and n % 4 == 3:
            return -1 * jacobi(n, a)
        else:
            return jacobi(n, a)


# computes the greatest common denominator of a and b.  assumes a > b
def gcd(a, b):
    while b != 0:
        c = a % b
        a = b
        b = c
    # a is returned if b == 0
    return a


# solovay-strassen primality test.  tests if num is prime
def SS(num, iConfidence):
    # ensure confidence of t
    for i in range(iConfidence):
        # choose random a between 1 and n-2
        a = random.randint(1, num - 1)

        # if a is not relatively prime to n, n is composite
        if gcd(a, num) > 1:
            return False

        # declares n prime if jacobi(a, n) is congruent to a^((n-1)/2) mod n
        if not jacobi(a, num) % num == pow(a, (num - 1) // 2, num):
            return False

    # if there have been t iterations without failure, num is believed to be prime
    return True


# find n bit prime
def find_prime(iNumBits, iConfidence):
    # keep testing until one is found
    while 1:
        # generate potential prime randomly
        p = random.randint(2 ** (iNumBits - 2), 2 ** (iNumBits - 1))
        # make sure it is odd
        while p % 2 == 0:
            p = random.randint(2 ** (iNumBits - 2), 2 ** (iNumBits - 1))

        # keep doing this if the solovay-strassen test fails
        while not SS(p, iConfidence):
            p = random.randint(2 ** (iNumBits - 2), 2 ** (iNumBits - 1))
            while p % 2 == 0:
                p = random.randint(2 ** (iNumBits - 2), 2 ** (iNumBits - 1))

        # if p is prime compute p = 2*p + 1
        # if p is prime, we have succeeded; else, start over
        p = p * 2 + 1
        if SS(p, iConfidence):
            return p


# encodes bytes to integers mod p.  reads bytes from file
def encode(byte_array: bytearray, iNumBits) -> list:
    # z is the array of integers mod p
    z = []

    # each encoded integer will be a linear combination of k message bytes
    # k must be the number of bits in the prime divided by 8 because each
    # message byte is 8 bits long
    k = iNumBits // 8

    # j marks the jth encoded integer
    # j will start at 0 but make it -k because j will be incremented during first iteration
    j = -1 * k
    # num is the summation of the message bytes
    num = 0
    # i iterates through byte array
    for i in range(len(byte_array)):
        # if i is divisible by k, start a new encoded integer
        if i % k == 0:
            j += k
            num = 0
            z.append(0)
        # add the byte multiplied by 2 raised to a multiple of 8
        z[j // k] += byte_array[i] * (2 ** (8 * (i % k)))

    # example
    # if n = 24, k = n / 8 = 3
    # z[0] = (summation from i = 0 to i = k)m[i]*(2^(8*i))
    # where m[i] is the ith message byte

    # return array of encoded integers
    return z


# decodes integers to the original message bytes
def decode(aiPlaintext, iNumBits) -> bytearray:
    # bytes array will hold the decoded original message bytes
    bytes_array = []

    # same deal as in the encode function.
    # each encoded integer is a linear combination of k message bytes
    # k must be the number of bits in the prime divided by 8 because each
    # message byte is 8 bits long
    k = iNumBits // 8

    # num is an integer in list aiPlaintext
    for num in aiPlaintext:
        # get the k message bytes from the integer, i counts from 0 to k-1
        for i in range(k):
            # temporary integer
            temp = num
            # j goes from i+1 to k-1
            for j in range(i + 1, k):
                # get remainder from dividing integer by 2^(8*j)
                temp = temp % (2 ** (8 * j))
            # message byte representing a letter is equal to temp divided by 2^(8*i)
            letter = temp // (2 ** (8 * i))
            # add the message byte letter to the byte array
            bytes_array.append(letter)
            # subtract the letter multiplied by the power of two from num so
            # so the next message byte can be found
            num = num - (letter * (2 ** (8 * i)))

    # example
    # if "You" were encoded.
    # Letter        #ASCII
    # Y              89
    # o              111
    # u              117
    # if the encoded integer is 7696217 and k = 3
    # m[0] = 7696217 % 256 % 65536 / (2^(8*0)) = 89 = 'Y'
    # 7696217 - (89 * (2^(8*0))) = 7696128
    # m[1] = 7696128 % 65536 / (2^(8*1)) = 111 = 'o'
    # 7696128 - (111 * (2^(8*1))) = 7667712
    # m[2] = 7667712 / (2^(8*2)) = 117 = 'u'

    decoded_bytearray = bytearray(b for b in bytes_array)

    return decoded_bytearray


class ElGamal:
    class PrivateKey:
        def __init__(self, p=None, g=None, x=None, iNumBits=None):
            self.p = p
            self.g = g
            self.x = x
            self.iNumBits = iNumBits

        def __repr__(self):
            return f"ElGamal.PrivateKey(p={self.p}, g={self.g}, x={self.x})"

        def __eq__(self, pk):
            return self.p == pk.p and self.g == pk.g and self.x == pk.x

        def __str__(self):
            return json.dumps(
                {"p": self.p, "g": self.g, "x": self.x, "iNumBits": self.iNumBits}
            )

        @classmethod
        def from_str(cls, s):
            obj = json.loads(s)
            return cls(obj["p"], obj["g"], obj["x"], obj["iNumBits"])

    class PublicKey:
        def __init__(self, p=None, g=None, h=None, iNumBits=None):
            self.p = p
            self.g = g
            self.h = h
            self.iNumBits = iNumBits

        def __repr__(self):
            return f"ElGamal.PublicKey(p={self.p}, g={self.g}, h={self.h})"

        def __eq__(self, pk):
            return self.p == pk.p and self.g == pk.g and self.h == pk.h

        def __str__(self):
            return json.dumps(
                {"p": self.p, "g": self.g, "h": self.h, "iNumBits": self.iNumBits}
            )

        @classmethod
        def from_str(cls, s):
            obj = json.loads(s)
            return cls(obj["p"], obj["g"], obj["h"], obj["iNumBits"])

    class Ciphertext:
        def __init__(self, cm, cr, pk):
            self.cm = cm  # ciphertext with message
            self.cr = cr  # ciphertext with random number
            self.pk = pk  # the public key

        def __neg__(self):
            try:
                new_cm = multiplicative_inverse(self.cm, self.pk.p)
                new_cr = multiplicative_inverse(self.cr, self.pk.p)
            except:
                print(self.cm, self.pk.p)
            return ElGamal.Ciphertext(new_cm, new_cr, self.pk)

        def __add__(self, e):
            # the base case for built-in sum()
            if isinstance(e, int) and e == 0:
                return ElGamal.Ciphertext(self.cm, self.cr, self.pk)

            # homomorphic operation
            assert self.pk == e.pk, "The public keys should be the same!"
            new_cm = self.cm * e.cm % self.pk.p
            new_cr = self.cr * e.cr % self.pk.p
            return ElGamal.Ciphertext(new_cm, new_cr, self.pk)

        def __radd__(self, e):
            return self + e

        def __sub__(self, e):
            return self + (-e)

        def __rmul__(self, scalar):
            if not isinstance(scalar, int):
                ValueError("only scalar multiplication is allowed")
            ret = ElGamal.Encrypt(self.pk, 0, 0)
            # fast multiplication
            for b in bin(scalar)[2:]:
                ret = ret + ret
                if b == "1":
                    ret += self
            return ret

        def __eq__(self, e):
            return self.cm == e.cm and self.cr == e.cr and self.pk == e.pk

        def __repr__(self):
            return f"ElGamal.Ciphertext(cm={self.cm}, cr={self.cr}, pk={self.pk})"

        def __str__(self):
            return json.dumps({"cm": self.cm, "cr": self.cr, "pk": str(self.pk)})

        @classmethod
        def from_str(cls, s):
            obj = json.loads(s)
            pk = ElGamal.PublicKey.from_str(obj["pk"])
            return cls(obj["cm"], obj["cr"], pk)

    @classmethod
    def KeyGen(cls, iNumBits=512, iConfidence=32):
        # p is the prime
        # g is the primitve root
        # x is random in (0, p-1) inclusive
        # h = g ^ x mod p
        p = find_prime(iNumBits, iConfidence)
        g = find_primitive_root(p)
        g = pow(g, 2, p)
        x = random.randint(1, (p - 1) // 2)
        h = pow(g, x, p)
        return (
            ElGamal.PublicKey(p, g, h, iNumBits),
            ElGamal.PrivateKey(p, g, x, iNumBits),
        )

    @classmethod
    def Encrypt(cls, pk, m, alpha=None):
        if type(m) == int:
            if alpha is None:
                alpha = cls.genAlpha(pk.p)
            cm = m * pow(pk.h, alpha, pk.p) % pk.p
            cr = pow(pk.g, alpha, pk.p)
            return ElGamal.Ciphertext(cm, cr, pk)
        else:
            z = encode(m, pk.iNumBits)
            ret = []
            for i in z:
                if alpha is None:
                    alpha = cls.genAlpha(pk.p)
                cm = i * pow(pk.h, alpha, pk.p) % pk.p
                cr = pow(pk.g, alpha, pk.p)
                ret.append(ElGamal.Ciphertext(cm, cr, pk))
            return ret

    @classmethod
    def Decrypt(cls, sk, ciphertexts):
        if type(ciphertexts) == ElGamal.Ciphertext:
            # s = cr^x mod p
            s = pow(ciphertexts.cr, sk.x, sk.p)
            # plaintext integer = cm*s^-1 mod p
            plain_int = (ciphertexts.cm * pow(s, sk.p - 2, sk.p)) % sk.p
            return plain_int
        else:
            z = []
            for c in ciphertexts:
                # s = cr^x mod p
                s = pow(c.cr, sk.x, sk.p)
                # plaintext integer = cm*s^-1 mod p
                z.append((c.cm * pow(s, sk.p - 2, sk.p)) % sk.p) 
            decrypted = decode(z, sk.iNumBits)
            # 删除末尾的\x00
            return decrypted.rstrip(b"\x00")

    @classmethod
    def ReEncrypt(cls, pk, ciphertext, alpha_prime=None):
        # 生成一个新的随机数alpha_prime用于重加密
        if alpha_prime is None:
            alpha_prime = cls.genAlpha(pk.p)

        # 计算重加密的两个部分
        cm_re = (
            pow(pk.g, 0, pk.p) * pow(pk.h, alpha_prime, pk.p) % pk.p
        )  # E(0, alpha_prime)的第一部分
        cr_re = pow(pk.g, alpha_prime, pk.p)  # E(0, alpha_prime)的第二部分

        # 同态相乘原密文和新密文
        new_cm = (ciphertext.cm * cm_re) % pk.p
        new_cr = (ciphertext.cr * cr_re) % pk.p

        # 返回新的重加密后的密文
        return ElGamal.Ciphertext(new_cm, new_cr, pk)

    @classmethod
    def genAlpha(cls, p):
        return randrange(p - 1)
