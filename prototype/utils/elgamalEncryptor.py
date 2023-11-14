try:
    from . import elgamal  # 尝试相对导入
except ImportError:
    import elgamal  # 回退到绝对导入
import pickle
from Crypto.Random.random import randrange


class ElgamalEncryptor:
    # 构造函数 输入公私钥文件
    def __init__(self, public_key_file=None, private_key_file=None):
        self.pk = None
        self.sk = None
        if public_key_file:
            with open(public_key_file, 'rb') as f:
                tmp = pickle.load(f)
            self.pk = elgamal.ElGamal.PublicKey.from_str(tmp)
        if private_key_file:
            with open(private_key_file, 'rb') as f:
                tmp = pickle.load(f)
            self.sk = elgamal.ElGamal.PrivateKey.from_str(tmp)
        

    # 生成密钥对
    @classmethod
    def generateAndSaveKeys(cls, public_key_file, private_key_file, bits=256):
        pk, sk = elgamal.ElGamal.KeyGen(bits)
        with open(public_key_file, 'wb') as f:
            pickle.dump(str(pk), f)
        with open(private_key_file, 'wb') as f:
            pickle.dump(str(sk), f)

    # 用公钥加密
    def encrypt(self, msg, alpha = None):
        if self.pk is None:
            return False
        return elgamal.ElGamal.Encrypt(self.pk, msg, alpha)

    # 用私钥解密
    def decrypt(self, ciphertext, message_space):
        if self.sk is None:
            return False
        return elgamal.ElGamal.Decrypt(self.sk, ciphertext, message_space)

    # 用公钥重加密
    def reEncrypt(self, ciphertext, alpha_prime = None):
        if self.pk is None:
            return False
        return elgamal.ElGamal.ReEncrypt(self.pk, ciphertext, alpha_prime)

    def genAlpha(self):
        return elgamal.ElGamal.genAlpha(self.pk.p)

    # 重加密交互式证明的模拟器    
    def proveReEncrypt(self, alpha):
        # 模拟证明过程的3次通信
        # 证明者知道e, alpha，且e=E(0, alpha)，而验证者仅知道e
        # 证明者需要在不透露alpha的情况下向验证者证明e=E(0, alpha)

        # 1.证明者发送e'
        alpha_prime = randrange(self.pk.p - 1)
        e_prime = self.encrypt(0, alpha_prime)  # e' = E(0, alpha')
        
        # 2.验证者发送一个挑战c
        c = randrange(self.pk.p - 1)

        # 3.证明者发送beta
        beta = (c * alpha + alpha_prime) % (self.pk.p-1)  # 计算响应beta
        
        return e_prime, c, beta
    
    # 验证重加密交互式证明模拟器的模拟结果
    def verifyReEncrypt(self, e, e_prime, c, beta):
        # 模拟最终的验证过程
        # 检查E(0, beta)是否等于c * e * e'
        # 对于ElGamal密文，我们需要分别计算每个组件
        tmp = self.encrypt(0, beta)
        
        # 计算c * e * e' 的第一部分 (对应于ElGamal密文的cm)
        e1 = (pow(e.cm, c, self.pk.p) * e_prime.cm) % self.pk.p

        # 计算c * e * e' 的第二部分 (对应于ElGamal密文的cr)
        e2 = (pow(e.cr, c, self.pk.p) * e_prime.cr) % self.pk.p

        # 现在，我们将 E(0, beta) 的两部分与上面计算的两部分进行比较
        return tmp.cm == e1 and tmp.cr == e2


if __name__=="__main__":

    # 首次运行前需要生成密钥对并保存
    ElgamalEncryptor.generateAndSaveKeys('tmp/keypairs/pk.pkl', 'tmp/keypairs/sk.pkl', 256)

    # 使用保存的密钥对初始化ElgamalEncryptor实例
    pk_file = 'tmp/keypairs/pk.pkl'
    sk_file = 'tmp/keypairs/sk.pkl'
    encryptor = ElgamalEncryptor(pk_file, sk_file)

    # 1.加密
    # 加密的输入是byte_array（即每个元素在0-255之间的整数数组）
    message_space = list(range(1000))
    msg = 123
    ciphertext = encryptor.encrypt(msg)
    print("Encrypted:", ciphertext)

    # 2.重加密（需要实现re_encrypt方法）
    alpha_prime = encryptor.genAlpha()
    new_ciphertext = encryptor.reEncrypt(ciphertext, alpha_prime)
    print("Re_encrypted:", new_ciphertext)

    # 3.解密
    decrypted_arr = encryptor.decrypt(ciphertext, message_space)
    decrypted_arr_re = encryptor.decrypt(new_ciphertext, message_space)
    print("Decrypted:", decrypted_arr)
    print("Decrypted_re:", decrypted_arr_re)

    # 4.重加密证明
    e_prime, c, beta = encryptor.proveReEncrypt(alpha_prime)
    valid = encryptor.verifyReEncrypt(new_ciphertext - ciphertext, e_prime, c, beta)
    print(f"Reencryption Proof Valid: {valid}")
