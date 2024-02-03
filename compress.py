def binary(number, keep_prefix=False):
    binarized = bin(number)
    if keep_prefix:
        return binarized
    return binarized[2:]


def unary(number):
    clause = ''
    if number:
        clause = number*'1'
    return clause + '0'


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


def get_size(bin_clause):
    return len(bin_clause)


if __name__ == "__main__":
    _numbers = [0, 54, 692, 833, 1502, 1802]
    print('Numbers:', _numbers)

    _binarized = list(map(binary, _numbers))
    _variable_code = list(map(variable_byte, _numbers))
    _gamma_code = list(map(gamma, _numbers))
    print('\nBinary Form')
    print('Primary Data: ', _binarized)
    print('Variable Byte: ', _variable_code)
    print('Gamma Code: ', _gamma_code)

    print('\nSize (bits)')
    print('Primary Data: ', sum(map(get_size, _binarized)))
    print('Variable Byte: ', sum(map(get_size, _variable_code)))
    print('Gamma Code: ', sum(map(get_size, _gamma_code)))
