from Crypto.Random.random import randrange
from ElGamal import ElGamal

class ReencryptionProof:
    def __init__(self, pk):
        self.pk = pk

    def prove(self, alpha):
        # 模拟证明过程的3次通信
        # 证明者知道e, alpha，且e=E(0, alpha)，而验证者仅知道e
        # 证明者需要在不透露alpha的情况下向验证者证明e=E(0, alpha)

        # 1.证明者发送e'
        alpha_prime = randrange(self.pk.p - 1)
        e_prime = self.encrypt(0, alpha_prime)  # e' = E(0, alpha')
        
        # 2.验证者发送一个挑战c
        c = self.challenge()  

        # 3.证明者发送beta
        beta = (c * alpha + alpha_prime) % (self.pk.p-1)  # 计算响应beta
        
        return e_prime, c, beta

    def verify(self, e, e_prime, c, beta):
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

    def encrypt(self, m, alpha=None):
        # ElGamal 加密
        return ElGamal.Encrypt(self.pk, m, alpha)
    
    def re_encrypt(self, m, alpha):
        # ElGamal 加密
        return ElGamal.ReEncrypt(self.pk, m, alpha)

    def challenge(self):
        # 生成一个随机挑战
        return randrange(self.pk.p - 1)


def test_reencryption_proof():
    # 证明密文B是密文A基于随机数alpha的重加密，等价于为证明密文B-A是0基于随机数alpha的密文
    # 我们现在可以使用sigma协议，给定数值0的任意Elgamal加密密文，证明【拥有加密得到该密文时用到的随机数alpha】
    # 为了证明密文B-A是0基于随机数alpha的密文，我们只需证明拥有 加密得到密文B-A时使用的随机数alpha

    # Initialize ElGamal system parameters
    pk, sk = ElGamal.KeyGen(256)  # Generate public and private keys
    
    # Initialize the reencryption proof system
    proof_system = ReencryptionProof(pk)

    # Encrypt the message m to get ciphertext A
    m = 123
    A = proof_system.encrypt(m) 

    # Re-encrypt A to get ciphertext B using a new random alpha
    alpha_prime = ElGamal.genAlpha(pk.p)  # Generate new random alpha for re-encryption
    B = proof_system.re_encrypt(A, alpha_prime)

    # Prove that B-A is an encryption of 0 using the known random number alpha
    e_prime, c, beta = proof_system.prove(alpha_prime)

    # Verify the proof that A_minus_B is an encryption of 0
    valid = proof_system.verify(B - A, e_prime, c, beta)

    # Output the verification result
    print(f"Reencryption Proof Valid: {valid}")

# Run the test function
test_reencryption_proof()
