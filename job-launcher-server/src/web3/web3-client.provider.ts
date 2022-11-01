import Web3 from "web3";
import { Provider } from "@nestjs/common";
import { WEB3_CLIENT, WEB3_MODULE_OPTIONS } from "./web3.constants";
import { v4 } from "uuid";
import { IWeb3ModuleAsyncOptions, IWeb3ModuleOptions } from "./interfaces";

export class Web3ClientError extends Error {}
export interface IWeb3Client {
  key: string;
  clients: Map<string, Web3>;
}

export const getClient = (options: IWeb3ModuleOptions): Web3 => {
  const { url } = options;
  return new Web3(url);
};

export const createClient = (): Provider => ({
  provide: WEB3_CLIENT,
  useFactory: async (options: IWeb3ModuleOptions | IWeb3ModuleOptions[]): Promise<IWeb3Client> => {
    const clients = new Map<string, Web3>();
    const defaultKey = v4();

    if (Array.isArray(options)) {
      await Promise.all(
        options.map(opt => {
          const key = opt.name || defaultKey;
          if (clients.has(key)) throw new Web3ClientError("Web3 client already exists");

          clients.set(key, getClient(opt));
          return true;
        }),
      );
    } else {
      const key = options.name || defaultKey;
      clients.set(key, getClient(options));
    }

    return {
      key: defaultKey,
      clients,
    };
  },
  inject: [WEB3_MODULE_OPTIONS],
});

export const createAsyncClientOptions = (options: IWeb3ModuleAsyncOptions): any => ({
  provide: WEB3_MODULE_OPTIONS,
  useFactory: options.useFactory,
  inject: options.inject,
});
