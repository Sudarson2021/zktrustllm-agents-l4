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
        vk.alpha = Pairing.G1Point(uint256(0x088799223e7a67fc9d06aa9e16320e15f5ff5c8f832a3b6e11c41cd000a6026e), uint256(0x15fe1f51502c7c8e8c1395e0d99acb7cd6f40d98767e061acbac158d92d0bdff));
        vk.beta = Pairing.G2Point([uint256(0x15bb1ea619d187145f37258ba43b0698581d1bc97f3bdc583089eb1a576272f6), uint256(0x0e633ef8766021c8dfd45f3280dc9b506142032575919e37e987252a829f6a44)], [uint256(0x0746d3530d220352b962576bef415edea42fb2b1d5e057a7568719afade64882), uint256(0x174862e0b8bf62058b953b53d9f1a0b1c386217f620d0f1dddaf7843cdd0b6a2)]);
        vk.gamma = Pairing.G2Point([uint256(0x1057f943245a6a30eaf666618dae81e7c512155d663b4692ca754e3dac224935), uint256(0x1900dd29022e6341da00622988cd923b1604c6b6d1592dab3290fd053f03f6ee)], [uint256(0x2e595ba350b485b852ae5d9090931bf2ad1962d7ec9401f9c3d74f4f362bc6b8), uint256(0x1fefca362b867f082929ae624d0f3476236edb3d1b21146bdf86a201cf86ffbb)]);
        vk.delta = Pairing.G2Point([uint256(0x263c5dfe25b86f9b59baf0f377b5cd07c7cacfdb675be7c091e9a20c71bf9377), uint256(0x1e50e4a24ef5947d88f788e385710618007e15b8230946fccc24fbfaf34a15ed)], [uint256(0x00101ea12f21e709bd13ff5ee37a984ae27aa895afd2c84eb4abd7b9fbd4b60c), uint256(0x25c180dc5dca253105ad8172d518d2a446857628369896ae83b4be379904a298)]);
        vk.gamma_abc = new Pairing.G1Point[](10);
        vk.gamma_abc[0] = Pairing.G1Point(uint256(0x145191c0cc1ca7d32533b131392a41152c50c22dbe8415420ed32923659eeb69), uint256(0x214603256b3f6dd5063e21b268360d8678ce7c0af5bd2046335d0332eccb598b));
        vk.gamma_abc[1] = Pairing.G1Point(uint256(0x152bb7df316d2d67f7ed424986fc4386237705de30a30288e4b63679fff658b2), uint256(0x0c24af39d26c3139aaef7cdf2b6578383e5bab4921e0d4adb2e6f6e96e3fafc3));
        vk.gamma_abc[2] = Pairing.G1Point(uint256(0x253b86f4a6afb45b7192c01b567a1cf454f6db4b89fc7db32950c4580ed09398), uint256(0x0cd126bd555e3b358d5aaa2bdb7c2c9acf8c1174b272bbcc0d3591959acb0659));
        vk.gamma_abc[3] = Pairing.G1Point(uint256(0x126ea25de9cd461ceadd10554c5f8e9ef38ecb083d74dbad06fa5aa465c43e53), uint256(0x17cf44d46ec1883c11c8a14e90e370e99146d0179f242a467fac4a4bcf3d76dd));
        vk.gamma_abc[4] = Pairing.G1Point(uint256(0x10c4d7207b91416412bcd209892022796074dfe5b1b9afaf30b5f46729a93613), uint256(0x04a523b58a5c74cc47b4e05e6f6141db3742702cf89a80bee4a50e687a1200f3));
        vk.gamma_abc[5] = Pairing.G1Point(uint256(0x1d2db711c057ddcd39d65cc7c28351f7c1ad34451f8e91ead9744c50539b47b1), uint256(0x2f8b09954439b07da51fc58d718cae7a1e53cbd72087096cb34ec370090128b6));
        vk.gamma_abc[6] = Pairing.G1Point(uint256(0x28dc45f7b86a7c68d43adffd13ab8bbdcf3b5dc9f83320eea87890eeb5fb6c10), uint256(0x204a5bd940fe1e0c6b9710f3cb506fff53e0119f8e9d0e25a1c08bd124726053));
        vk.gamma_abc[7] = Pairing.G1Point(uint256(0x055e81d52b008446c4e26ef835f544301f21645cee8d97eaa9c93183b7c09931), uint256(0x2d5c1ab7b2341c1635c0ab0a0c2edbb82e17e920599ce67430614e18786163a1));
        vk.gamma_abc[8] = Pairing.G1Point(uint256(0x148ff2a01ca148900726b1efdc08dd5d4c444f9db9598b613d32ed2e89a75d69), uint256(0x0dcc18001edc8546c646a27244e2b6c5e3c10f4b962d745966b3d387981d5c4d));
        vk.gamma_abc[9] = Pairing.G1Point(uint256(0x2c4f79770116db0046e796dd9e945dd52764eeee24a8bd6c50c188d9f8388a00), uint256(0x25052bbccf588a0da90ce07b958b88a6098b9c49ddda604e23b83a9cc1a7cb60));
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
            Proof memory proof, uint[9] memory input
        ) public view returns (bool r) {
        uint[] memory inputValues = new uint[](9);
        
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
