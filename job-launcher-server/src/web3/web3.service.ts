import { Inject, Injectable } from "@nestjs/common";
import { IWeb3Client, Web3ClientError } from "./web3-client.provider";
import { WEB3_CLIENT } from "./web3.constants";
import Web3 from "web3";
import { ConfigService } from "@nestjs/config";

@Injectable()
export class Web3Service {
  public tokenAddress: string;

  constructor(
    @Inject(WEB3_CLIENT)
    private readonly web3Client: IWeb3Client,
    private readonly configService: ConfigService,
  ) {
    this.tokenAddress = this.configService.get("WEB3_REQUESTER_ADDRESS", "");
  }

  public getClient(name?: string): Web3 {
    if (!name) name = this.web3Client.key;

    if (!this.web3Client.clients.has(name)) throw new Web3ClientError("Web3 client does not exists");

    const web3 = this.web3Client.clients.get(name);

    if (!web3) throw new Web3ClientError("Web3 client does not exists");

    return web3;
  }

  getClients(): Map<string, Web3> {
    return this.web3Client.clients;
  }
}
