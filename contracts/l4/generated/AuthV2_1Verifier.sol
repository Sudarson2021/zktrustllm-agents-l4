// This file is MIT Licensed.
//
// Copyright 2017 Christian Reitwiessner
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
pragma solidity ^0.8.0;
library Pairing {
    struct G1Point {
        uint X;
        uint Y;
    }
    // Encoding of field elements is: X[0] * z + X[1]
    struct G2Point {
        uint[2] X;
        uint[2] Y;
    }
    /// @return the generator of G1
    function P1() pure internal returns (G1Point memory) {
        return G1Point(1, 2);
    }
    /// @return the generator of G2
    function P2() pure internal returns (G2Point memory) {
        return G2Point(
            [10857046999023057135944570762232829481370756359578518086990519993285655852781,
             11559732032986387107991004021392285783925812861821192530917403151452391805634],
            [8495653923123431417604973247489272438418190587263600148770280649306958101930,
             4082367875863433681332203403145435568316851327593401208105741076214120093531]
        );
    }
    /// @return the negation of p, i.e. p.addition(p.negate()) should be zero.
    function negate(G1Point memory p) pure internal returns (G1Point memory) {
        // The prime q in the base field F_q for G1
        uint q = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
        if (p.X == 0 && p.Y == 0)
            return G1Point(0, 0);
        return G1Point(p.X, q - (p.Y % q));
    }
    /// @return r the sum of two points of G1
    function addition(G1Point memory p1, G1Point memory p2) internal view returns (G1Point memory r) {
        uint[4] memory input;
        input[0] = p1.X;
        input[1] = p1.Y;
        input[2] = p2.X;
        input[3] = p2.Y;
        bool success;
        assembly {
            success := staticcall(sub(gas(), 2000), 6, input, 0xc0, r, 0x60)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid() }
        }
        require(success);
    }


    /// @return r the product of a point on G1 and a scalar, i.e.
    /// p == p.scalar_mul(1) and p.addition(p) == p.scalar_mul(2) for all points p.
    function scalar_mul(G1Point memory p, uint s) internal view returns (G1Point memory r) {
        uint[3] memory input;
        input[0] = p.X;
        input[1] = p.Y;
        input[2] = s;
        bool success;
        assembly {
            success := staticcall(sub(gas(), 2000), 7, input, 0x80, r, 0x60)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid() }
        }
        require (success);
    }
    /// @return the result of computing the pairing check
    /// e(p1[0], p2[0]) *  .... * e(p1[n], p2[n]) == 1
    /// For example pairing([P1(), P1().negate()], [P2(), P2()]) should
    /// return true.
    function pairing(G1Point[] memory p1, G2Point[] memory p2) internal view returns (bool) {
        require(p1.length == p2.length);
        uint elements = p1.length;
        uint inputSize = elements * 6;
        uint[] memory input = new uint[](inputSize);
        for (uint i = 0; i < elements; i++)
        {
            input[i * 6 + 0] = p1[i].X;
            input[i * 6 + 1] = p1[i].Y;
            input[i * 6 + 2] = p2[i].X[1];
            input[i * 6 + 3] = p2[i].X[0];
            input[i * 6 + 4] = p2[i].Y[1];
            input[i * 6 + 5] = p2[i].Y[0];
        }
        uint[1] memory out;
        bool success;
        assembly {
            success := staticcall(sub(gas(), 2000), 8, add(input, 0x20), mul(inputSize, 0x20), out, 0x20)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid() }
        }
        require(success);
        return out[0] != 0;
    }
    /// Convenience method for a pairing check for two pairs.
    function pairingProd2(G1Point memory a1, G2Point memory a2, G1Point memory b1, G2Point memory b2) internal view returns (bool) {
        G1Point[] memory p1 = new G1Point[](2);
        G2Point[] memory p2 = new G2Point[](2);
        p1[0] = a1;
        p1[1] = b1;
        p2[0] = a2;
        p2[1] = b2;
        return pairing(p1, p2);
    }
    /// Convenience method for a pairing check for three pairs.
    function pairingProd3(
            G1Point memory a1, G2Point memory a2,
            G1Point memory b1, G2Point memory b2,
            G1Point memory c1, G2Point memory c2
    ) internal view returns (bool) {
        G1Point[] memory p1 = new G1Point[](3);
        G2Point[] memory p2 = new G2Point[](3);
        p1[0] = a1;
        p1[1] = b1;
        p1[2] = c1;
        p2[0] = a2;
        p2[1] = b2;
        p2[2] = c2;
        return pairing(p1, p2);
    }
    /// Convenience method for a pairing check for four pairs.
    function pairingProd4(
            G1Point memory a1, G2Point memory a2,
            G1Point memory b1, G2Point memory b2,
            G1Point memory c1, G2Point memory c2,
            G1Point memory d1, G2Point memory d2
    ) internal view returns (bool) {
        G1Point[] memory p1 = new G1Point[](4);
        G2Point[] memory p2 = new G2Point[](4);
        p1[0] = a1;
        p1[1] = b1;
        p1[2] = c1;
        p1[3] = d1;
        p2[0] = a2;
        p2[1] = b2;
        p2[2] = c2;
        p2[3] = d2;
        return pairing(p1, p2);
    }
}

contract Verifier {
    using Pairing for *;
    struct VerifyingKey {
        Pairing.G1Point alpha;
        Pairing.G2Point beta;
        Pairing.G2Point gamma;
        Pairing.G2Point delta;
        Pairing.G1Point[] gamma_abc;
    }
    struct Proof {
        Pairing.G1Point a;
        Pairing.G2Point b;
        Pairing.G1Point c;
    }
    function verifyingKey() pure internal returns (VerifyingKey memory vk) {
        vk.alpha = Pairing.G1Point(uint256(0x14c349c334c430b5de11a54f5a7766afe5f28a289ce033cd25eb1f9d746a823d), uint256(0x195bd3db76552217fc6f011297c2e8936c739fab4f346164d77db857f17fb5a5));
        vk.beta = Pairing.G2Point([uint256(0x1eb068a4a594c69f9f1cc41f9338212fc9b48381d9b68623f90ba7f6954fd467), uint256(0x0b404d56513b1b51e749f2b2a51e8fbfc64a3e0bc1efb427693fc2ef9a4a769a)], [uint256(0x00ee3ce7d4c07e7a1e3d84ced4e3a4ef669f2c0be3f56c35c3d42b914e258451), uint256(0x258be6064fd4948097b52a11e50193a3cae8baa0b359339cdf36a13225ecb894)]);
        vk.gamma = Pairing.G2Point([uint256(0x1a87544ce22e9170a821b908ca001a3522ad17ae88b16485aa1ddad1ad66c89d), uint256(0x2d807320388a3f961754efb782f63d6778d4146dde954ef6bb4170fcb8ff3a2d)], [uint256(0x1c9e3bd8b60d030ac34e858500095d4a532f0b2f6fc61a61e284a5a7ea59020e), uint256(0x0bd7f95f1d66324e88449e435b395b19585757f56451b0d8b6391c0fb6d81e7b)]);
        vk.delta = Pairing.G2Point([uint256(0x076e24b3b2b3ba720e2cd039f7d7d75bf517470055f3753bf51eab17e3f33296), uint256(0x0ae6c51044a1e3dfa0f0633ae149a0091e842fec028506e8dd62082ab0b52c85)], [uint256(0x280f4c68a33189174a4b8bdadac11679f0c77ce713d93e7e881db95d1ddd686e), uint256(0x1a0c2173963cea7bf8b95e23c3858c1eb57b3dbb4d81ec3d389c08b8f508de26)]);
        vk.gamma_abc = new Pairing.G1Point[](9);
        vk.gamma_abc[0] = Pairing.G1Point(uint256(0x2ebb1c0f9a5c4f536e700365b78baaf29dba91211d3f8172edc9daeb4e0841b2), uint256(0x183bf61396e373a9749e92769dde4514e889a419b264aaadedc5fcb6bb643c59));
        vk.gamma_abc[1] = Pairing.G1Point(uint256(0x1d6750ceb512906a8571606077b2bd381f77a0b7a29bf473398845de9bf59593), uint256(0x013a50e01c1c2ebc3891bde9e5ec83632a32ed24989ac07d51cc2500a8076bac));
        vk.gamma_abc[2] = Pairing.G1Point(uint256(0x2abb26633d67f697b855959fef123eb0b98007eb6ce70eb3a22b76aaed8d271d), uint256(0x1ca47927c37ff4f41cd904d6bc4b06c7d333853ddd620ab287d720696e2fbce0));
        vk.gamma_abc[3] = Pairing.G1Point(uint256(0x1544437947bb76f818cae8f0aeed783f6c2f6abf18d7ce8b9ec8123d59f77bf6), uint256(0x062696cbbec6838ecfb7e369ce574152aa245b504662894b22c3679b8394f25d));
        vk.gamma_abc[4] = Pairing.G1Point(uint256(0x04ab8fc54ceff514e5eb6a6364d18f096ed428d110646b9e2e3f025157ac1b13), uint256(0x04a29bc82a26bdeb240fcae06adc0eef9bcbf740c1530fcf72f4acbce1ba6786));
        vk.gamma_abc[5] = Pairing.G1Point(uint256(0x22078d883f29e1a1f29bee366e40930895cf09893440d331cf0199938b88e265), uint256(0x2a68e3f134d2f0a19ff71658b44c02e53bbb2c24a561438b8e46a17f84f4ed85));
        vk.gamma_abc[6] = Pairing.G1Point(uint256(0x211c4e2d3f7571ab0281bea87e01f0573b5d37e6f70b60ea3344a9f1e68ae924), uint256(0x2215b8291565f322db55dce021bac3453a06608477fb28085385eeeb7cf2338a));
        vk.gamma_abc[7] = Pairing.G1Point(uint256(0x06f7dce6556249f0cb5959f046deb61ebf7392345d06827c6629cbda9e4198d7), uint256(0x2155d2a7cb2c7b14436bb74e5b7cb05afd2bbd0116d6d9f30c6f305df1e1993c));
        vk.gamma_abc[8] = Pairing.G1Point(uint256(0x02f6c5ed6f0517c8d155e26f2155eca2bbb7fd3f50cf6019cf460ec7252aac1d), uint256(0x168de49a07d998bd92968d7248d21d50efc7432aa32cfbb6ee52a4fe6c9622fe));
    }
    function verify(uint[] memory input, Proof memory proof) internal view returns (uint) {
        uint256 snark_scalar_field = 21888242871839275222246405745257275088548364400416034343698204186575808495617;
        VerifyingKey memory vk = verifyingKey();
        require(input.length + 1 == vk.gamma_abc.length);
        // Compute the linear combination vk_x
        Pairing.G1Point memory vk_x = Pairing.G1Point(0, 0);
        for (uint i = 0; i < input.length; i++) {
            require(input[i] < snark_scalar_field);
            vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.gamma_abc[i + 1], input[i]));
        }
        vk_x = Pairing.addition(vk_x, vk.gamma_abc[0]);
        if(!Pairing.pairingProd4(
             proof.a, proof.b,
             Pairing.negate(vk_x), vk.gamma,
             Pairing.negate(proof.c), vk.delta,
             Pairing.negate(vk.alpha), vk.beta)) return 1;
        return 0;
    }
    function verifyTx(
            Proof memory proof, uint[8] memory input
        ) public view returns (bool r) {
        uint[] memory inputValues = new uint[](8);
        
        for(uint i = 0; i < input.length; i++){
            inputValues[i] = input[i];
        }
        if (verify(inputValues, proof) == 0) {
            return true;
        } else {
            return false;
        }
    }
}
