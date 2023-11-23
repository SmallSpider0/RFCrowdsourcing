import json

from Crypto.Util.number import inverse as multiplicative_inverse
from Crypto.Math.Primality import generate_probable_safe_prime
from Crypto.Math.Numbers import Integer
from Crypto.Random.random import randrange


class ElGamal:
    class PrivateKey:
        def __init__(self, p=None, g=None, x=None):
            self.p = p
            self.g = g
            self.x = x

        def __repr__(self):
            return f"ElGamal.PrivateKey(p={self.p}, g={self.g}, x={self.x})"

        def __eq__(self, pk):
            return self.p == pk.p and self.g == pk.g and self.x == pk.x

        def __str__(self):
            return json.dumps({"p": self.p, "g": self.g, "x": self.x})

        @classmethod
        def from_str(cls, s):
            obj = json.loads(s)
            return cls(obj["p"], obj["g"], obj["x"])

    class PublicKey:
        def __init__(self, p=None, g=None, h=None):
            self.p = p
            self.g = g
            self.h = h

        def __repr__(self):
            return f"ElGamal.PublicKey(p={self.p}, g={self.g}, h={self.h})"

        def __eq__(self, pk):
            return self.p == pk.p and self.g == pk.g and self.h == pk.h

        def __str__(self):
            return json.dumps({"p": self.p, "g": self.g, "h": self.h})

        @classmethod
        def from_str(cls, s):
            obj = json.loads(s)
            return cls(obj["p"], obj["g"], obj["h"])

    class Ciphertext:
        def __init__(self, cm, cr, pk):
            self.cm = cm  # ciphertext with message
            self.cr = cr  # ciphertext with random number
            self.pk = pk  # the public key

        def __neg__(self):
            new_cm = multiplicative_inverse(self.cm, self.pk.p)
            new_cr = multiplicative_inverse(self.cr, self.pk.p)
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
    def KeyGen(cls, nbits=512):
        # generate prime
        p = generate_probable_safe_prime(exact_bits=nbits)

        # generate group generator
        # reference: https://github.com/Legrandin/pycryptodome/blob/master/lib/Crypto/PublicKey/ElGamal.py#L62
        while 1:
            g = pow(Integer.random_range(min_inclusive=2, max_exclusive=p), 2, p)
            if g in (1, 2):
                continue
            if (p - 1) % g == 0:
                continue
            ginv = g.inverse(p)
            if (p - 1) % ginv == 0:
                continue
            break

        p, g = int(p), int(g)

        x = randrange(nbits + 1, p)
        h = pow(g, x, p)

        return (ElGamal.PublicKey(p, g, h), ElGamal.PrivateKey(p, g, x))

    # @classmethod
    # def Encrypt(cls, pk, m, alpha=None):
    #     if alpha is None:
    #         alpha = cls.genAlpha(pk.p)
    #     cm = pow(pk.g, m, pk.p) * pow(pk.h, alpha, pk.p) % pk.p
    #     cr = pow(pk.g, alpha, pk.p)
    #     return ElGamal.Ciphertext(cm, cr, pk)

    @classmethod
    def Encrypt(cls, pk, m, alpha=None):
        if alpha is None:
            alpha = cls.genAlpha(pk.p)
        cm = m * pow(pk.h, alpha, pk.p) % pk.p
        cr = pow(pk.g, alpha, pk.p)
        return ElGamal.Ciphertext(cm, cr, pk)

    @classmethod
    def Decrypt(cls, sk, c):
        # s = cr^x mod p
        s = pow(c.cr, sk.x, sk.p)
        # plaintext integer = cm*s^-1 mod p
        plain = (c.cm * pow(s, sk.p - 2, sk.p)) % sk.p
        return plain

    @classmethod
    def ReEncrypt(cls, pk, ciphertext, alpha_prime=None):
        """
        对ElGamal密文进行重加密，不需要原始消息或私钥。
        """
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