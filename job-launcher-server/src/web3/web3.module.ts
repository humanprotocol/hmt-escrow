import { DynamicModule, Module } from "@nestjs/common";
import { IWeb3ModuleAsyncOptions, IWeb3ModuleOptions } from "./interfaces";
import { Web3CoreModule } from "./web3-core.module";

@Module({})
export class Web3Module {
  static forRoot(options: IWeb3ModuleOptions | IWeb3ModuleOptions[]): DynamicModule {
    return {
      module: Web3Module,
      imports: [Web3CoreModule.register(options)],
    };
  }

  static forRootAsync(options: IWeb3ModuleAsyncOptions): DynamicModule {
    return {
      module: Web3Module,
      imports: [Web3CoreModule.forRootAsync(options)],
    };
  }
}
