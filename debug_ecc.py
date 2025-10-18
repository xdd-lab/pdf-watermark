import reedsolo

rs = reedsolo.RSCodec(16)
data = b'Test'
print(f'Input: {data}')
encoded = rs.encode(data)
print(f'Encoded: {encoded}, type: {type(encoded)}')
decoded = rs.decode(encoded)
print(f'Decoded: {decoded}, type: {type(decoded)}')
print(f'Are they equal? {data in decoded or decoded == data}')
