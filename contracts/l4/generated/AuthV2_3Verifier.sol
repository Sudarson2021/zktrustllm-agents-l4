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
        vk.alpha = Pairing.G1Point(uint256(0x2d39d862bc7edb010ce635b4c6d112298af94787f29f0fd862906b9b481b452d), uint256(0x0f03873ef806fef9dfa27423810acd015a1320ab837e2839c2df6296f8f617b3));
        vk.beta = Pairing.G2Point([uint256(0x094249259f8f4179fc451c4f4d91c982709f05efa73507632db087ef959869e7), uint256(0x1a3b26f8b1187bdd5d918c78a92897fd1b754bf718845b0115d06a62a2f57e3a)], [uint256(0x218e09b67174822031bd4f04473977032105445be6cf61c35ca8d4127977a902), uint256(0x2dd43101d69f16512d2fa0d8206e81c43f4bd1af9de27bef5de3ce6fe0b35de9)]);
        vk.gamma = Pairing.G2Point([uint256(0x13331c7903dd4946f66a8681be680801d53980b91731a42beb81e0b0f09c1085), uint256(0x08176d9e98c4d5226517038c4bcd7ec3b84e694127a04656aea27f220242cb46)], [uint256(0x14ece1633707504211636526a167a820a0983341b009538fa0dd14cb547b3349), uint256(0x29e0c8e8bdad7b421d7f9ed75a3d283d53a8ff0b840416518569d5da3a622563)]);
        vk.delta = Pairing.G2Point([uint256(0x005baf358f1c7ba0e150abef1fe710a97e6dbb631a7d74b3656a5a9a2d6404a6), uint256(0x03367da53f00f2c38bd5652e46c1c31b2efd0917cf6ea052a94f882c6c83df82)], [uint256(0x21d76309cc8e11e6abd4bba95f10443a4e0b6c34e5c543ff007d8d20d20f77df), uint256(0x2b26587aa4b3682fe4d0b869006309184abe16ee48741d41e7d66a038aee678a)]);
        vk.gamma_abc = new Pairing.G1Point[](13);
        vk.gamma_abc[0] = Pairing.G1Point(uint256(0x03f3dad856281e04c50122a537ced6658b745593377f221039c930894919a53d), uint256(0x04a196937b0a18fb83c6e7f5fac424d8de1bc68d52cd23c045a8e70e8ba70547));
        vk.gamma_abc[1] = Pairing.G1Point(uint256(0x08975af7094d701a2a0e55fbe115d789c320054732cd2e2baafe12cbb697d3c7), uint256(0x057941bf224c313d801f0af564643b1fb48dedb03347e314e64a9f82ffb999a7));
        vk.gamma_abc[2] = Pairing.G1Point(uint256(0x25c0d21b022c9f7820806d2aa044605f3510df8c5d92007e5d68d78f6274dfc5), uint256(0x0eb2f3870740904e8ee0286eeb9e1ada82dfd94a4b1cfa274a78f2b7804e1a2a));
        vk.gamma_abc[3] = Pairing.G1Point(uint256(0x0633d71c7e0b6dd5150fd41ef7320278a160cd4cacf11f52feb4f4ab8ad4dd6e), uint256(0x29c2867fb05eeeac85e2364ccadec6d64359fd97d38aef6b29225d7974b71ada));
        vk.gamma_abc[4] = Pairing.G1Point(uint256(0x043df4d10f2fc656cb3fe3988e76703b808505528bde162d2403ce200e013039), uint256(0x2366f725310f19eba7e55504b20194bacaf701821cb9138f276a61135de7d301));
        vk.gamma_abc[5] = Pairing.G1Point(uint256(0x2e83d661f3045843a7dfbd4a268921a900b9a82bab60335368ef6a675d0206cf), uint256(0x213c64ac0cd62110f44101c411a84a663df81fbf6591327c95198be17fdf6bde));
        vk.gamma_abc[6] = Pairing.G1Point(uint256(0x16fd9164c71f951be2a28a680658285f15bddf01cb5d00ad6e44b7d6dbabea8a), uint256(0x21bcd0cc5b35ba4faecd1121cf838fe7debcfaf710e2140da539f1dc52b6ae25));
        vk.gamma_abc[7] = Pairing.G1Point(uint256(0x1ac3f8bf50363dc3e093312c7db89b434fe1bc75b8e54d2e50f10920d0c47b88), uint256(0x0384e3368abdd5419f9bc623941145b33212c0c86cfbf3c773defe78568ea620));
        vk.gamma_abc[8] = Pairing.G1Point(uint256(0x0b05174884a12273f81c047a6b2c0b8f67ded9af1ac47d8f24f9753721a8d245), uint256(0x068141f01ba1b158b93bdbc3e6eff9d496454c487ba1b7b82cf8c3684ed254a7));
        vk.gamma_abc[9] = Pairing.G1Point(uint256(0x146b64db39a751eee949ac36c94e015330e6eff32e0bcc11f2e85d64d4b97137), uint256(0x19374def48ae208da1ed80ff2566a741f61453004d5e6a5d3f348013a9f3a650));
        vk.gamma_abc[10] = Pairing.G1Point(uint256(0x1c1f346594da2acdea23754d403a4dae7b3ad30d2c4c473075aeadffe67a305e), uint256(0x2d5c0075fc9d14bc6479069c1a61c8b5568e504857f65c09684151400f09913e));
        vk.gamma_abc[11] = Pairing.G1Point(uint256(0x2ecb7487ff01018c1d0f2ad1026c4d1c7e3329a6ebeec4ca6ef26ca6ed7179bc), uint256(0x01faafa7c4103b675b7dc7ad01e0f2a73278cab2418a76fb5d08295343735b98));
        vk.gamma_abc[12] = Pairing.G1Point(uint256(0x14509c63dd1530ebacd2a92df23a75a03ccddcd7740335689825d105688dfdf5), uint256(0x07b038a758edec2a4bb3e90152b0623bb82c5d807d5f2cad543b5ca54ea3c2f6));
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
            Proof memory proof, uint[12] memory input
        ) public view returns (bool r) {
        uint[] memory inputValues = new uint[](12);
        
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
