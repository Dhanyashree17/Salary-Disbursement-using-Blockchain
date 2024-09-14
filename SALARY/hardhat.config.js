require("@nomiclabs/hardhat-waffle");

module.exports = {
    solidity: {
      compilers: [
        {
          version: "0.8.0",
        },
      ],
    },
    networks: {
      localhost: {
        url: "http://127.0.0.1:8545",
      },
    },
  };