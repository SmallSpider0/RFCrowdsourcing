import elgamal
import pickle

class ElgamalEncryptor:
    # 构造函数
    def __init__(self, public_key_file, private_key_file):
        with open(public_key_file, 'rb') as f:
            public_key = pickle.load(f)
        with open(private_key_file, 'rb') as f:
            private_key = pickle.load(f)
        self.public_key = public_key
        self.private_key = private_key
     
    # 生成密钥对
    @staticmethod
    def generate_and_save_keys(public_key_file, private_key_file, bits=256):
        key_pair = elgamal.generate_keys(bits)
        public_key = key_pair['publicKey']
        private_key = key_pair['privateKey']

        with open(public_key_file, 'wb') as f:
            pickle.dump(public_key, f)
        with open(private_key_file, 'wb') as f:
            pickle.dump(private_key, f)

    def encrypt(self, msg, pub_key=None):
        if pub_key is None:
            pub_key = self.public_key
        return elgamal.encrypt(pub_key, msg)

    def decrypt(self, ciphertext):
        return elgamal.decrypt(self.private_key, ciphertext)

    def re_encrypt(self, ciphertext):
        # 这里的public_key仅用于提供群的阶和生成元
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
    # ElgamalEncryptor.generate_and_save_keys('tmp/public_key.pkl', 'tmp/private_key.pkl', 256)

    # 使用保存的密钥对初始化ElgamalEncryptor实例
    encryptor = ElgamalEncryptor('tmp/public_key.pkl', 'tmp/private_key.pkl')    

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
