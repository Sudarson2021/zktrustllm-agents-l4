// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AnomalyLedger {
    struct AnomalyRecord {
        string agentId;
        string severity;
        string traceCID;
        bytes32 anomalyCommitment;
        uint256 timestamp;
    }

    uint256 public anomalyCount;
    mapping(uint256 => AnomalyRecord) public anomalies;

    event AnomalyLogged(
        uint256 indexed anomalyId,
        string agentId,
        string severity,
        string traceCID,
        bytes32 anomalyCommitment
    );

    function logAnomaly(
        string memory _agentId,
        string memory _severity,
        string memory _traceCID,
        bytes32 _anomalyCommitment
    ) external returns (uint256) {
        anomalyCount += 1;

        anomalies[anomalyCount] = AnomalyRecord({
            agentId: _agentId,
            severity: _severity,
            traceCID: _traceCID,
            anomalyCommitment: _anomalyCommitment,
            timestamp: block.timestamp
        });

        emit AnomalyLogged(
            anomalyCount,
            _agentId,
            _severity,
            _traceCID,
            _anomalyCommitment
        );

        return anomalyCount;
    }
}
