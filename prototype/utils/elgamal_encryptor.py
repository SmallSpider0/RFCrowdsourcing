# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from utils.elgamal import ElGamal

# 系统库
import pickle
from Crypto.Random.random import randrange
from multiprocessing import Lock
import time


class ElgamalEncryptor:
    # 构造函数 输入公私钥文件
    def __init__(self, public_key_str, private_key_str=None):
        self.pk = ElGamal.PublicKey.from_str(public_key_str)
        self.totaltime = 0
        self.totaltimeLock = Lock()
        if private_key_str != None:
            self.sk = ElGamal.PrivateKey.from_str(private_key_str)

    # 生成密钥对
    @classmethod
    def generateAndSaveKeys(
        cls, public_key_file, private_key_file, iNumBits=256, iConfidence=32
    ):
        pk, sk = ElGamal.KeyGen(iNumBits, iConfidence)
        with open(public_key_file, "wb") as f:
            pickle.dump(str(pk), f)
        with open(private_key_file, "wb") as f:
            pickle.dump(str(sk), f)

    @classmethod
    def createCiphertext(cls, s):
        return ElGamal.Ciphertext.from_str(s)

    # 用公钥加密
    def encrypt(self, msg, alpha=None):
        if self.pk is None:
            return False
        st = time.time()
        ret = ElGamal.Encrypt(self.pk, msg, alpha)
        end = time.time()
        with self.totaltimeLock:
            self.totaltime += end - st
        return ret

    # 用私钥解密
    def decrypt(self, ciphertexts):
        if self.sk is None:
            return False
        st = time.time()
        ret = ElGamal.Decrypt(self.sk, ciphertexts)
        end = time.time()
        with self.totaltimeLock:
            self.totaltime += end - st
        return ret

    # 用公钥重加密
    def reEncrypt(self, ciphertexts, alpha_prime=None):
        if self.pk is None:
            return False
        # 对每个密文对象运行重加密
        st = time.time()
        if type(ciphertexts) == list:
            ret = []
            for ciphertext in ciphertexts:
                ret.append(ElGamal.ReEncrypt(self.pk, ciphertext, alpha_prime))
        else:
            ret = ElGamal.ReEncrypt(self.pk, ciphertexts, alpha_prime)
        end = time.time()
        with self.totaltimeLock:
            self.totaltime += end - st
        return ret

    def genAlpha(self):
        return ElGamal.genAlpha(self.pk.p)

    # 重加密证明通信内容 1/3
    def proveReEncrypt_1(self):
        # 1.证明者发送e'
        st = time.time()
        alpha_tmp = randrange(self.pk.p - 1)
        e_prime = self.encrypt(0, alpha_tmp)  # e' = E(0, alpha')
        end = time.time()
        with self.totaltimeLock:
            self.totaltime += end - st
        return e_prime, alpha_tmp

    # 重加密证明通信内容 2/3
    def proveReEncrypt_2(self):
        # 2.验证者发送一个挑战c
        st = time.time()
        c = randrange(self.pk.p - 1)
        end = time.time()
        with self.totaltimeLock:
            self.totaltime += end - st
        return c

    # 重加密证明通信内容 3/3
    def proveReEncrypt_3(self, c, alpha, alpha_tmp) -> int:
        # 3.证明者基于挑战c构造并发送beta
        st = time.time()
        beta = (c * alpha + alpha_tmp) % (self.pk.p - 1)  # 计算响应beta
        end = time.time()
        with self.totaltimeLock:
            self.totaltime += end - st
        return beta

    # 验证重加密交互式证明模拟器的模拟结果
    def verifyReEncrypt(self, new_ciphertexts, ciphertexts, e_prime, c, beta):
        def verify(new_ciphertext, ciphertext):
            # 模拟最终的验证过程
            # 检查E(0, beta)是否等于c * e * e'
            # 对于ElGamal密文，我们需要分别计算每个组件
            st = time.time()
            e = new_ciphertext - ciphertext
            tmp = self.encrypt(0, beta)
            # 计算c * e * e' 的第一部分 (对应于ElGamal密文的cm)
            e1 = (pow(e.cm, c, self.pk.p) * e_prime.cm) % self.pk.p
            # 计算c * e * e' 的第二部分 (对应于ElGamal密文的cr)
            e2 = (pow(e.cr, c, self.pk.p) * e_prime.cr) % self.pk.p
            end = time.time()
            with self.totaltimeLock:
                self.totaltime += end - st
            # 现在，我们将 E(0, beta) 的两部分与上面计算的两部分进行比较
            return tmp.cm == e1 and tmp.cr == e2

        if type(ciphertexts) == list:
            if len(new_ciphertexts) != len(ciphertexts):
                return False
            # 验证每个密文
            for i in range(len(new_ciphertexts)):
                if not verify(new_ciphertexts[i], ciphertexts[i]):
                    return False
            return True
        else:
            return verify(new_ciphertexts, ciphertexts)


if __name__ == "__main__":
    import time
    from Crypto.Util.number import inverse as multiplicative_inverse

    # 首次运行前需要生成密钥对并保存
    # st = time.time()
    # ElgamalEncryptor.generateAndSaveKeys(
    #     "tmp/pk.pkl", "tmp/sk.pkl", 256, 32
    # )
    # print(time.time() - st)

    # 使用保存的密钥对初始化ElgamalEncryptor实例
    pk_file = "tmp/keypairs/pk2048.pkl"
    sk_file = "tmp/keypairs/sk2048.pkl"
    with open(pk_file, "rb") as f:
        public_key_str = pickle.load(f)
    with open(sk_file, "rb") as f:
        private_key_str = pickle.load(f)
    encryptor = ElgamalEncryptor(public_key_str, private_key_str)

    def homo_test(encryptor):
        for _ in range(10000):
            msg = randrange(1, 10000)
            ciphertext = encryptor.encrypt(msg)
            alpha_prime = encryptor.genAlpha()
            new_ciphertext = encryptor.reEncrypt(ciphertext, alpha_prime)

            try:
                c1 = -new_ciphertext
            except:
                print(msg)

    def performance_test(encryptor):
        results = [[] for _ in range(4)]
        msg = 500000

        for _ in range(1):
            t0 = time.time()
            # 1.加密
            ciphertext = encryptor.encrypt(msg)

            t1 = time.time()
            # 2.重加密（需要实现re_encrypt方法）
            alpha_prime = encryptor.genAlpha()
            new_ciphertext = encryptor.reEncrypt(ciphertext, alpha_prime)

            t2 = time.time()
            # 3.解密
            decrypted = encryptor.decrypt(ciphertext)

            t3 = time.time()
            # 4.重加密证明
            (
                e_prime,
                alpha_tmp,
            ) = encryptor.proveReEncrypt_1()  # 证明者发送e_prime，并保存alpha_tmp
            c = encryptor.proveReEncrypt_2()  # 验证者发送一个挑战c
            beta = encryptor.proveReEncrypt_3(c, alpha_prime, alpha_tmp)  # 证明者发送beta
            valid = encryptor.verifyReEncrypt(
                new_ciphertext, ciphertext, e_prime, c, beta
            )  # 验证者验证上述交互内容，判断重加密是否正确
            t4 = time.time()
            results[0].append(t1 - t0)
            results[1].append(t2 - t1)
            results[2].append(t3 - t2)
            results[3].append(t4 - t3)
        for res in results:
            print(f"{sum(res)/len(res):.6f}")

    # 功能测试
    def base_test(encryptor):
        # 1.加密
        msg = 1234
        ciphertexts = encryptor.encrypt(msg.to_bytes(8, byteorder="big", signed=True))
        # print("Encrypted:", ciphertexts)

        # ciphertext_file = "tmp/ciphertext.pkl"
        # with open(ciphertext_file, "wb") as f:
        #     pickle.dump(str(ciphertexts), f)

        # # 2.重加密
        alpha_prime = encryptor.genAlpha()
        new_ciphertexts = encryptor.reEncrypt(ciphertexts, alpha_prime)
        # print("Re_encrypted:", new_ciphertexts)

        # # 3.同态性质
        # cipher_0 = new_ciphertexts[0] - ciphertexts[0]

        # # 4.解密
        decrypted = encryptor.decrypt(ciphertexts)
        # decrypted_re = encryptor.decrypt(new_ciphertexts)
        print(decrypted)
        # decrypted_ho = encryptor.decrypt(cipher_0)
        print("Decrypted:", int.from_bytes(decrypted, byteorder="big", signed=True))
        # print("Decrypted_re:", list(decrypted_re))
        # print("Decrypted_ho:", decrypted_ho)

        # # 5.重加密证明
        e_prime, alpha_tmp = encryptor.proveReEncrypt_1()  # 证明者发送e_prime，并保存alpha_tmp
        c = encryptor.proveReEncrypt_2()  # 验证者发送一个挑战c
        beta = encryptor.proveReEncrypt_3(c, alpha_prime, alpha_tmp)  # 证明者发送beta
        valid = encryptor.verifyReEncrypt(
            new_ciphertexts, ciphertexts, e_prime, c, beta
        )  # 验证者验证上述交互内容，判断重加密是否正确
        print(f"Reencryption Proof Valid: {valid}")

    base_test(encryptor)
    print(encryptor.totaltime)
