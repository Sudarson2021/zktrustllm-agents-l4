require("dotenv").config();
require("@nomicfoundation/hardhat-toolbox");

function getSepoliaAccounts() {
  const pk = process.env.SEPOLIA_PRIVATE_KEY || "";
  if (/^0x[0-9a-fA-F]{64}$/.test(pk)) return [pk];
  if (/^[0-9a-fA-F]{64}$/.test(pk)) return ["0x" + pk];
  return [];
}

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      viaIR: true
    }
  },
  networks: {
    localhost: { url: "http://127.0.0.1:8545" },
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: getSepoliaAccounts(),
      chainId: 11155111
    }
  },
  etherscan: {
    apiKey: {
      sepolia: process.env.ETHERSCAN_API_KEY || ""
    }
  },
  mocha: { timeout: 120000 }
};
