import { ethers } from 'ethers';
import { toast } from 'react-toastify';
import { setTx } from '../../services/redux/slices/jobSlice';
import { store } from '../../services/redux/store';

const HMTokenAbi = require('../../contracts/HMTokenAbi.json');

export const transferERC20 = async ({
  fundAmount,
  backdropCallback,
}: {
  fundAmount: number;
  backdropCallback: any;
}) => {
  let txHash: string = '';

  try {
    if (!window.ethereum) {
      toast.error(
        'Connect your Metamask wallet to update the message on the blockchain',
        {
          position: 'top-right',
        }
      );
    }

    // const isTransactionReceipt = async (transactionHash: string) => {
    //   const provider = new ethers.providers.Web3Provider(window.ethereum);
    //   const txReceipt = await provider.getTransactionReceipt(transactionHash);
    //   if (txReceipt && txReceipt.blockNumber) {
    //     return txReceipt;
    //   }
    // };

    const accounts = await window.ethereum.request({
      method: 'eth_requestAccounts',
    });

    const accountAddress = accounts[0];
    const value = ethers.utils.parseEther(String(fundAmount));

    const iface = new ethers.utils.Interface(HMTokenAbi);

    const data = iface.encodeFunctionData('transfer', [
      process.env.REACT_APP_JOB_LAUNCHER_ADDRESS,
      value,
    ]);

    const transactionParameters = {
      from: accountAddress,
      to: process.env.REACT_APP_HMT_TOKEN_ADDRESS,
      data,
    };

    await window.ethereum
      .request({
        method: 'eth_sendTransaction',
        params: [transactionParameters],
      })
      .then((hash: string) => {
        backdropCallback(false);

        txHash = hash;
        if (txHash) {
          store.dispatch(setTx({ hash: txHash }));
        }
      })
      .catch(() => {
        backdropCallback(false);
        toast.error('Please try again', {
          position: 'top-right',
        });
      });
  } catch (err) {
    backdropCallback(false);
    console.log(err);
  }
};
