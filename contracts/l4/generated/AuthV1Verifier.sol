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
        vk.alpha = Pairing.G1Point(uint256(0x00edf2b5288bb0138f143a141381db6d0ab8c730b030b4306d2427e6ec631f9c), uint256(0x0cef977f32d27ff5bd7383ce6126b60b38c71d8015e534d0242b5ab1d6713ab9));
        vk.beta = Pairing.G2Point([uint256(0x0fbcc6ebd192bda31ac5dabddc46ef961009b7836b0715a53ce6f1488678294a), uint256(0x242aa9d75b9964a918df8d4e6c331842a0ad3375fb59f94e73e287b4ed4345c1)], [uint256(0x247c5cc5896f95ae60d9918964766445d8f5fb9fa675fabf398af7706b61f5e5), uint256(0x1123447b0aa3bc7eacd5ffb5df90213f267390693625942158ff1419652f434f)]);
        vk.gamma = Pairing.G2Point([uint256(0x04cfbe28feab5cc1c9186dadb3ec0d40b19c021b2a1459460e687e91af7c77ca), uint256(0x1530663150bd1870814ebe7dfa9a54d14f2d2beccd4a3c4065bbbc500d6c0f46)], [uint256(0x0976a0b18a2190498f1d5bc5e8374bcdd465ee7d61dae8f8dd0c091f6a95560d), uint256(0x10a53d7849bf4cc2b7b6cbf46543a1736b815ad3d336f82ad2535b6d7b927c05)]);
        vk.delta = Pairing.G2Point([uint256(0x0dc1afd00d447e2812b00aae5c816aaebe7e9f8099f451818007b4cc3ef6b56b), uint256(0x0543dac59acbf221047cdbf671d8c97f32d4897f6f952dff456876974d274bc6)], [uint256(0x22499ff71d21ec87fa4d420928c890f658d401ba97268bb8d01e5c47714978b2), uint256(0x0858a92accee24df75710267814972dca4c8425c3c018eec1aaa228bd7023830)]);
        vk.gamma_abc = new Pairing.G1Point[](8);
        vk.gamma_abc[0] = Pairing.G1Point(uint256(0x21ed15f4846d01f59de3e8d76214a173636f5492e8250c47a7e3e558b6041e25), uint256(0x0ef91aed5ef0c4c1f5aa0ebb5a2284336ce94bba809cc283abd9c9c7a9059e7a));
        vk.gamma_abc[1] = Pairing.G1Point(uint256(0x082fe318d2182f69ad9e6f57713ed2b3d8538c325c618e884f98607feeb369f8), uint256(0x04bdae6a569fe02b042930dbc31d2e2d7ba6e54f871f7f6ba26321ea7b307ba7));
        vk.gamma_abc[2] = Pairing.G1Point(uint256(0x09cad6e5fc20be7ba5f8df026ca9a721522d5824edd82a827ba0114ee0f72ed9), uint256(0x097c8d94a47d1e4d68882458086a1a22783480b21cc0d69a36971c4af785a79b));
        vk.gamma_abc[3] = Pairing.G1Point(uint256(0x156542d260fb74c64287dbd45de70d04969fe0ec6dfe2a2b1b2cb007f5353780), uint256(0x2cfd25f82293cb96f0d3363939d94bee7f64ed27b84b753edbb0fb7fb5e39e25));
        vk.gamma_abc[4] = Pairing.G1Point(uint256(0x1b4e106240bb4af54002bf2ebde8059b907e1a01c14a7b9e471b6dfc3ab0368c), uint256(0x0c6efd25f03e8ba7a781bbf5855486962e079ff523c6b0fe79764f677a554555));
        vk.gamma_abc[5] = Pairing.G1Point(uint256(0x01215b6bd72441ff800c3e168dbbae5a0d30da47267993e3128c8f23a209cf83), uint256(0x1afee53a69a34cc675048c67174eb0e0ed3d177723abfde5960c8d0aefeb54af));
        vk.gamma_abc[6] = Pairing.G1Point(uint256(0x0ab02e9968c15e73a3d06d91e3781d9225fede8f5df826d21df93ad1f0a7eead), uint256(0x20fb0d2c588eece3ccdba13045822103926369b04ef68f01f8bfbf86ecb1642a));
        vk.gamma_abc[7] = Pairing.G1Point(uint256(0x10d59ff86ac7a3ae385d638f87fee334d9d4a1be47e0ad55485729b7b144d628), uint256(0x021a10de429268240d19680781794c67ec42e11e979f71426b805716ab950085));
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
            Proof memory proof, uint[7] memory input
        ) public view returns (bool r) {
        uint[] memory inputValues = new uint[](7);
        
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
