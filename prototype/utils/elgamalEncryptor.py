try:
    from . import elgamal  # 尝试相对导入
except ImportError:
    import elgamal  # 回退到绝对导入
import pickle

class ElgamalEncryptor:
    # 构造函数 输入公私钥文件
    def __init__(self, public_key_file=None, private_key_file=None):
        if public_key_file:
            with open(public_key_file, 'rb') as f:
                tmp = pickle.load(f)
                public_key = elgamal.PublicKey(tmp['p'],tmp['g'],tmp['h'],tmp['iNumBits'])
            self.public_key = public_key
        if private_key_file:
            with open(private_key_file, 'rb') as f:
                tmp = pickle.load(f)
                private_key = elgamal.PrivateKey(tmp['p'],tmp['g'],tmp['x'],tmp['iNumBits'])
            self.private_key = private_key
        

    # 生成密钥对
    @staticmethod
    def generate_and_save_keys(public_key_file, private_key_file, bits=256):
        key_pair = elgamal.generate_keys(bits)
        public_key = key_pair['publicKey']
        private_key = key_pair['privateKey']

        with open(public_key_file, 'wb') as f:
            pickle.dump(public_key.to_dict(), f)
        with open(private_key_file, 'wb') as f:
            pickle.dump(private_key.to_dict(), f)

    # 用公钥加密
    def encrypt(self, msg):
        if self.public_key is None:
            return False
        return elgamal.encrypt(self.public_key, msg)

    # 用私钥解密
    def decrypt(self, ciphertext):
        if self.private_key is None:
            return False
        return elgamal.decrypt(self.private_key, ciphertext)

    # 用公钥重加密
    def re_encrypt(self, ciphertext):
        if self.public_key is None:
            return False
        return elgamal.reencrypt(self.public_key, ciphertext)

    # 预留用于ZKP算法的接口
    def generate_nizkp(self):
        # 这里添加生成NIZKP的逻辑
        raise NotImplementedError("ZKP generation needs to be implemented.")

    def verify_nizkp(self):
        # 这里添加验证NIZKP的逻辑
        raise NotImplementedError("ZKP verification needs to be implemented.")


if __name__=="__main__":

    # 首次运行前需要生成密钥对并保存
    ElgamalEncryptor.generate_and_save_keys('tmp/keypairs/requester_pk.pkl', 'tmp/keypairs/requester_sk.pkl', 256)

    # 使用保存的密钥对初始化ElgamalEncryptor实例
    pk_file = 'tmp/keypairs/requester_pk.pkl'
    sk_file = 'tmp/keypairs/requester_sk.pkl'
    encryptor = ElgamalEncryptor(pk_file, sk_file)

    # 1.加密
    # 加密的输入是byte_array（即每个元素在0-255之间的整数数组）
    byte_array = [123,233,23]
    ciphertext = encryptor.encrypt(byte_array)
    print("Encrypted:", ciphertext)

    # 2.重加密（需要实现re_encrypt方法）
    new_ciphertext = encryptor.re_encrypt(ciphertext)
    print("Re_encrypted:", new_ciphertext)

    # 3.解密
    decrypted_arr = encryptor.decrypt(ciphertext)
    decrypted_arr_re = encryptor.decrypt(new_ciphertext)
    print("Decrypted:", decrypted_arr)
    print("Decrypted_re:", decrypted_arr_re)
