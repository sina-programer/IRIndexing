def binary(number, prefix=False):
    binarized = bin(number)
    if prefix:
        return binarized
    return binarized[2:]

def unary(number):
    return '1'*number + '0'

def gamma(number):
    if number == 0:
        return None
    number_b = binary(number)
    offset = number_b[1:]
    return unary(len(offset)) + offset

def variable_byte(number, n=8):
    np = n-1
    result = ''
    number_b = binary(number)
    n_packs = (len(number_b) // n) + 1
    for i in range(n_packs):
        pack = format(number_b[i*np : (i+1)*np], f'0>{np}')
        is_last_iter = i == n_packs-1
        if is_last_iter:
            result = '1' + pack + result
        else:
            result = '0' + pack + result
    return result

def get_size(x):
    if isinstance(x, int):
        return x.bit_length()
    elif isinstance(x, (str, bytes)):
        return len(x)


if __name__ == "__main__":
    test_cases = [
        'binary(5)',
        'unary(5)',
        'gamma(5)',
        'variable_byte(5)',
        'get_size(5)'
    ]
    for case in test_cases:
        print(f"{case} = {eval(case)}")
    print()
