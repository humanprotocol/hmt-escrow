import { DynamicModule, Global, Inject, Module, OnModuleDestroy } from "@nestjs/common";
import { WEB3_CLIENT, WEB3_MODULE_OPTIONS } from "./web3.constants";
import { createAsyncClientOptions, createClient, IWeb3Client } from "./web3-client.provider";
import { HttpProviderBase } from "web3-core-helpers";
import { Web3Service } from "./web3.service";
import { IWeb3ModuleAsyncOptions, IWeb3ModuleOptions } from "./interfaces";
import { ConfigModule } from "@nestjs/config";

@Global()
@Module({
  providers: [Web3Service],
  exports: [Web3Service],
})
export class Web3CoreModule implements OnModuleDestroy {
  constructor(
    @Inject(WEB3_MODULE_OPTIONS)
    private readonly options: IWeb3ModuleOptions | IWeb3ModuleOptions[],
    @Inject(WEB3_CLIENT)
    private readonly web3Client: IWeb3Client,
  ) {}

  static register(options: IWeb3ModuleOptions | IWeb3ModuleOptions[]): DynamicModule {
    return {
      module: Web3CoreModule,
      providers: [createClient(), { provide: WEB3_MODULE_OPTIONS, useValue: options }],
      exports: [Web3Service],
      imports: [ConfigModule]
    };
  }

  static forRootAsync(options: IWeb3ModuleAsyncOptions): DynamicModule {
    return {
      module: Web3CoreModule,
      imports: options.imports,
      providers: [createClient(), createAsyncClientOptions(options)],
      exports: [Web3Service],
    };
  }

  onModuleDestroy(): void {
    const closeConnection =
      ({ clients, key }: IWeb3Client) =>
      (options: IWeb3ModuleOptions) => {
        const name = options.name || key;
        const client = clients.get(name);

        if (client) {
          const provider = client.currentProvider as HttpProviderBase;
          provider.disconnect();
        }
      };

    const closeClientConnection = closeConnection(this.web3Client);

    if (Array.isArray(this.options)) {
      this.options.forEach(closeClientConnection);
    } else {
      closeClientConnection(this.options);
    }
  }
}
