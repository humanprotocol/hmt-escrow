export interface INetwork {
  title: string;
  key: string;
  scanner: string;
  rpcUrl: string;
  defaultFactoryAddr: string;
  hmtAddr: string;
  graphqlClientUrl: string;
  showTokenStats: boolean;
}

interface INetworkMap {
  [key: string]: INetwork;
}

export const networkMap: INetworkMap = {
  polygon: {
    title: 'Polygon Mainnet',
    key: 'polygon',
    scanner: 'https://polygonscan.com',
    rpcUrl: 'https://polygon-rpc.com/',
    defaultFactoryAddr: '0x45eBc3eAE6DA485097054ae10BA1A0f8e8c7f794',
    hmtAddr: '0xc748B2A084F8eFc47E086ccdDD9b7e67aEb571BF',
    graphqlClientUrl:
      'https://api.thegraph.com/subgraphs/name/humanprotocol/polygon',
    showTokenStats: true,
  },
  bsc: {
    title: 'Binance Smart Chain Mainnet',
    key: 'bsc',
    scanner: 'https://bscscan.com',
    rpcUrl: 'https://bsc-dataseed1.binance.org/',
    defaultFactoryAddr: '0xc88bC422cAAb2ac8812de03176402dbcA09533f4',
    hmtAddr: '0x0d501B743F22b641B8C8dfe00F1AAb881D57DDC7',
    graphqlClientUrl:
      'https://api.thegraph.com/subgraphs/name/humanprotocol/bsc',
    showTokenStats: true,
  },
  mumbai: {
    title: 'Polygon Mumbai Testnet',
    key: 'mumbai',
    scanner: 'https://mumbai.polygonscan.com',
    rpcUrl: 'https://rpc-mumbai.maticvigil.com',
    defaultFactoryAddr: '0x558cd800f9F0B02f3B149667bDe003284c867E94',
    hmtAddr: '0x0376D26246Eb35FF4F9924cF13E6C05fd0bD7Fb4',
    graphqlClientUrl:
      'https://api.thegraph.com/subgraphs/name/humanprotocol/mumbai',
    showTokenStats: true,
  },
  goerli: {
    title: 'Ethereum Goerli',
    key: 'goerli',
    scanner: 'https://goerli.etherscan.io',
    rpcUrl: 'https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',
    defaultFactoryAddr: '0xaAe6a2646C1F88763E62e0cD08aD050Ea66AC46F',
    hmtAddr: '0xd3A31D57FDD790725d0F6B78095F62E8CD4ab317',
    graphqlClientUrl:
      'https://api.thegraph.com/subgraphs/name/humanprotocol/goerli',
    showTokenStats: true,
  },
  neonslabdev: {
    title: 'NeonsLab Devtestnet',
    key: 'neonslabdev',
    scanner: 'https://neonscan.org',
    rpcUrl: 'https://proxy.devnet.neonlabs.org/solana',
    defaultFactoryAddr: '0x75D377773aCf9eB1076B01c1698415Bfe2db6D9d',
    hmtAddr: '',
    graphqlClientUrl: 'https://api.thegraph.com',
    // the graph is not implemented yet
    showTokenStats: false,
  },
  moonbeam: {
    title: 'Moonbeam Mainnet',
    key: 'moonbeam',
    scanner: 'https://moonbeam.moonscan.io',
    rpcUrl: 'https://rpc.api.moonbeam.network',
    defaultFactoryAddr: '0x98108c28B7767a52BE38B4860832dd4e11A7ecad',
    hmtAddr: '0x3b25BC1dC591D24d60560d0135D6750A561D4764',
    graphqlClientUrl:
      'https://api.thegraph.com/subgraphs/name/humanprotocol/moonbeam',
    showTokenStats: true,
  },
  bsctest: {
    title: 'Binance Smart Chain Testnet',
    key: 'bsctest',
    scanner: 'https://testnet.bscscan.com',
    rpcUrl: 'https://data-seed-prebsc-1-s1.binance.org:8545/',
    defaultFactoryAddr: '0xaae6a2646c1f88763e62e0cd08ad050ea66ac46f',
    hmtAddr: '0xd3a31d57fdd790725d0f6b78095f62e8cd4ab317',
    graphqlClientUrl:
      'https://api.thegraph.com/subgraphs/name/humanprotocol/bsctest',
    showTokenStats: true,
  },
  avalancheTestnet: {
    title: 'Fuji C-Chain',
    key: 'avalancheTestnet',
    scanner: 'https://testnet.snowtrace.io',
    rpcUrl: 'https://api.avax-test.network/ext/C/rpc',
    defaultFactoryAddr: '0xfb4469201951C3B9a7F1996c477cb7BDBEcE0A88',
    hmtAddr: '0x9406d5c635AD22b0d76c75E52De57A2177919ca3',
    graphqlClientUrl: 'https://api.thegraph.com',
    // the graph is not implemented yet
    showTokenStats: false,
  },
  avalanche: {
    title: 'Avalanche C-Chain Mainnet',
    key: 'avalanche',
    scanner: 'https://snowtrace.io',
    rpcUrl: 'https://api.avax.network/ext/bc/C/rpc',
    defaultFactoryAddr: '0x9767a578ba7a5FA1563c8229943cB01cd8446BB4',
    hmtAddr: '0x12365293cb6477d4fc2686e46BB97E3Fb64f1550',
    graphqlClientUrl: 'https://api.thegraph.com',
    // the graph is not implemented yet
    showTokenStats: false,
  },
};
export const networks = Object.values(networkMap).map((network) => network);
