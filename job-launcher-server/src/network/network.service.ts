import { Repository } from "typeorm";
import { Injectable, NotFoundException } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { ConfigService } from "@nestjs/config";

import { INetworkDto } from "./interfaces";
import { NetworkId } from "../common/constants/networks";

@Injectable()
export class NetworkService {
  private networks: INetworkDto[];

  constructor(
    private readonly configService: ConfigService,
  ) {
    this.networks = [{
      networkId: NetworkId.LOCAL_GANACHE,
      rpcApi: this.configService.get<string>("WEB3_PROVIDER_URL", ""),
      trustedJobLauncherAddr: this.configService.get<string>("WEB3_JOB_LAUNCHER_ADDRESS", ""),
      trustedExchangeOracleAddr: this.configService.get<string>("EXCHANGE_ORACLE_ADDRESS", ""),
      hmtAddr: this.configService.get<string>("WEB3_HMT_TOKEN", ""),
      factoryAddr: this.configService.get<string>("WEB3_ESCROW_FACTORY_ADDRESS", ""),
      privateKey: this.configService.get<string>("WEB3_OWNER_PRIVATE_KEY", ""),
    }]
  }

  public async getNetworkById(networkId: string): Promise<INetworkDto> {
    const network = this.networks.find(network => network.networkId === networkId)

    if (!network) throw new NotFoundException("Network not found");

    return network
  }

  public async getList(): Promise<INetworkDto[]> {
    return this.networks;
  }
}
