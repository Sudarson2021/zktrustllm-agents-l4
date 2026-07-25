// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @notice Minimal SHA-512 implementation for an isolated local gas
///         microbenchmark. It is deliberately not used by the deployable
///         evidence-anchor path.
/// @dev The implementation follows FIPS 180-4 for practical byte strings whose
///      bit length fits in uint64. Publication tests gate the empty-string and
///      "abc" FIPS vectors before any gas sample is accepted.
library Sha512Local {
    error MessageTooLong();

    function hash(bytes memory message) internal pure returns (bytes memory) {
        if (message.length > type(uint64).max / 8) revert MessageTooLong();

        uint256 paddedLength = message.length + 1 + 16;
        paddedLength = ((paddedLength + 127) / 128) * 128;
        bytes memory padded = new bytes(paddedLength);
        for (uint256 i = 0; i < message.length; ++i) {
            padded[i] = message[i];
        }
        padded[message.length] = 0x80;

        uint64 bitLength = uint64(message.length * 8);
        for (uint256 i = 0; i < 8; ++i) {
            padded[paddedLength - 1 - i] = bytes1(uint8(bitLength >> (i * 8)));
        }

        uint64[8] memory state = [
            uint64(0x6a09e667f3bcc908),
            uint64(0xbb67ae8584caa73b),
            uint64(0x3c6ef372fe94f82b),
            uint64(0xa54ff53a5f1d36f1),
            uint64(0x510e527fade682d1),
            uint64(0x9b05688c2b3e6c1f),
            uint64(0x1f83d9abfb41bd6b),
            uint64(0x5be0cd19137e2179)
        ];

        uint64[80] memory constants = [
            uint64(0x428a2f98d728ae22), uint64(0x7137449123ef65cd),
            uint64(0xb5c0fbcfec4d3b2f), uint64(0xe9b5dba58189dbbc),
            uint64(0x3956c25bf348b538), uint64(0x59f111f1b605d019),
            uint64(0x923f82a4af194f9b), uint64(0xab1c5ed5da6d8118),
            uint64(0xd807aa98a3030242), uint64(0x12835b0145706fbe),
            uint64(0x243185be4ee4b28c), uint64(0x550c7dc3d5ffb4e2),
            uint64(0x72be5d74f27b896f), uint64(0x80deb1fe3b1696b1),
            uint64(0x9bdc06a725c71235), uint64(0xc19bf174cf692694),
            uint64(0xe49b69c19ef14ad2), uint64(0xefbe4786384f25e3),
            uint64(0x0fc19dc68b8cd5b5), uint64(0x240ca1cc77ac9c65),
            uint64(0x2de92c6f592b0275), uint64(0x4a7484aa6ea6e483),
            uint64(0x5cb0a9dcbd41fbd4), uint64(0x76f988da831153b5),
            uint64(0x983e5152ee66dfab), uint64(0xa831c66d2db43210),
            uint64(0xb00327c898fb213f), uint64(0xbf597fc7beef0ee4),
            uint64(0xc6e00bf33da88fc2), uint64(0xd5a79147930aa725),
            uint64(0x06ca6351e003826f), uint64(0x142929670a0e6e70),
            uint64(0x27b70a8546d22ffc), uint64(0x2e1b21385c26c926),
            uint64(0x4d2c6dfc5ac42aed), uint64(0x53380d139d95b3df),
            uint64(0x650a73548baf63de), uint64(0x766a0abb3c77b2a8),
            uint64(0x81c2c92e47edaee6), uint64(0x92722c851482353b),
            uint64(0xa2bfe8a14cf10364), uint64(0xa81a664bbc423001),
            uint64(0xc24b8b70d0f89791), uint64(0xc76c51a30654be30),
            uint64(0xd192e819d6ef5218), uint64(0xd69906245565a910),
            uint64(0xf40e35855771202a), uint64(0x106aa07032bbd1b8),
            uint64(0x19a4c116b8d2d0c8), uint64(0x1e376c085141ab53),
            uint64(0x2748774cdf8eeb99), uint64(0x34b0bcb5e19b48a8),
            uint64(0x391c0cb3c5c95a63), uint64(0x4ed8aa4ae3418acb),
            uint64(0x5b9cca4f7763e373), uint64(0x682e6ff3d6b2b8a3),
            uint64(0x748f82ee5defb2fc), uint64(0x78a5636f43172f60),
            uint64(0x84c87814a1f0ab72), uint64(0x8cc702081a6439ec),
            uint64(0x90befffa23631e28), uint64(0xa4506cebde82bde9),
            uint64(0xbef9a3f7b2c67915), uint64(0xc67178f2e372532b),
            uint64(0xca273eceea26619c), uint64(0xd186b8c721c0c207),
            uint64(0xeada7dd6cde0eb1e), uint64(0xf57d4f7fee6ed178),
            uint64(0x06f067aa72176fba), uint64(0x0a637dc5a2c898a6),
            uint64(0x113f9804bef90dae), uint64(0x1b710b35131c471b),
            uint64(0x28db77f523047d84), uint64(0x32caab7b40c72493),
            uint64(0x3c9ebe0a15c9bebc), uint64(0x431d67c49c100d4c),
            uint64(0x4cc5d4becb3e42b6), uint64(0x597f299cfc657e2a),
            uint64(0x5fcb6fab3ad6faec), uint64(0x6c44198c4a475817)
        ];

        uint64[80] memory words;
        for (uint256 blockOffset = 0; blockOffset < paddedLength; blockOffset += 128) {
            for (uint256 i = 0; i < 16; ++i) {
                uint256 cursor = blockOffset + i * 8;
                uint64 word;
                for (uint256 j = 0; j < 8; ++j) {
                    word = (word << 8) | uint64(uint8(padded[cursor + j]));
                }
                words[i] = word;
            }
            for (uint256 i = 16; i < 80; ++i) {
                unchecked {
                    words[i] =
                        _smallSigma1(words[i - 2]) +
                        words[i - 7] +
                        _smallSigma0(words[i - 15]) +
                        words[i - 16];
                }
            }

            uint64 a = state[0];
            uint64 b = state[1];
            uint64 c = state[2];
            uint64 d = state[3];
            uint64 e = state[4];
            uint64 f = state[5];
            uint64 g = state[6];
            uint64 h = state[7];

            for (uint256 i = 0; i < 80; ++i) {
                unchecked {
                    uint64 t1 = h + _bigSigma1(e) + _choose(e, f, g) + constants[i] + words[i];
                    uint64 t2 = _bigSigma0(a) + _majority(a, b, c);
                    h = g;
                    g = f;
                    f = e;
                    e = d + t1;
                    d = c;
                    c = b;
                    b = a;
                    a = t1 + t2;
                }
            }

            unchecked {
                state[0] += a;
                state[1] += b;
                state[2] += c;
                state[3] += d;
                state[4] += e;
                state[5] += f;
                state[6] += g;
                state[7] += h;
            }
        }

        return abi.encodePacked(
            state[0], state[1], state[2], state[3],
            state[4], state[5], state[6], state[7]
        );
    }

    function _rotateRight(uint64 value, uint8 amount) private pure returns (uint64) {
        return (value >> amount) | (value << (64 - amount));
    }

    function _choose(uint64 x, uint64 y, uint64 z) private pure returns (uint64) {
        return (x & y) ^ (~x & z);
    }

    function _majority(uint64 x, uint64 y, uint64 z) private pure returns (uint64) {
        return (x & y) ^ (x & z) ^ (y & z);
    }

    function _bigSigma0(uint64 x) private pure returns (uint64) {
        return _rotateRight(x, 28) ^ _rotateRight(x, 34) ^ _rotateRight(x, 39);
    }

    function _bigSigma1(uint64 x) private pure returns (uint64) {
        return _rotateRight(x, 14) ^ _rotateRight(x, 18) ^ _rotateRight(x, 41);
    }

    function _smallSigma0(uint64 x) private pure returns (uint64) {
        return _rotateRight(x, 1) ^ _rotateRight(x, 8) ^ (x >> 7);
    }

    function _smallSigma1(uint64 x) private pure returns (uint64) {
        return _rotateRight(x, 19) ^ _rotateRight(x, 61) ^ (x >> 6);
    }
}

/// @title HashPrimitiveMicrobenchmark
/// @notice Local-only comparison of EVM hash execution paths.
/// @dev This contract is an experimental instrument. The production-oriented
///      HashCommitmentLedger computes SHA-512 off chain and anchors the entire
///      64-byte digest instead of running this Solidity implementation.
contract HashPrimitiveMicrobenchmark {
    function measureKeccak256(bytes calldata payload)
        external
        view
        returns (bytes memory digest, uint256 primitiveGas)
    {
        bytes memory input = payload;
        uint256 gasBefore = gasleft();
        bytes32 value = keccak256(input);
        primitiveGas = gasBefore - gasleft();
        digest = abi.encodePacked(value);
    }

    function measureSha256(bytes calldata payload)
        external
        view
        returns (bytes memory digest, uint256 primitiveGas)
    {
        bytes memory input = payload;
        uint256 gasBefore = gasleft();
        bytes32 value = sha256(input);
        primitiveGas = gasBefore - gasleft();
        digest = abi.encodePacked(value);
    }

    function measureSha512Local(bytes calldata payload)
        external
        view
        returns (bytes memory digest, uint256 primitiveGas)
    {
        bytes memory input = payload;
        uint256 gasBefore = gasleft();
        digest = Sha512Local.hash(input);
        primitiveGas = gasBefore - gasleft();
    }
}
