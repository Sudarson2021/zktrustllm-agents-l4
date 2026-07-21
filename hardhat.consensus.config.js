// Isolated Hardhat paths for the PoS/Roll-DPoS benchmark.
// The repository contains publication evidence under artifacts/, so benchmark
// compilation must never clean or rewrite that directory.
const base = require("./hardhat.config");

module.exports = {
  ...base,
  paths: {
    ...(base.paths || {}),
    artifacts: ".hardhat-consensus/artifacts",
    cache: ".hardhat-consensus/cache"
  }
};
