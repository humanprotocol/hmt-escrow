import { ModuleMetadata } from "@nestjs/common";

export interface IWeb3ModuleOptions {
  name?: string;
  url: string;
}

export interface IWeb3ModuleAsyncOptions extends Pick<ModuleMetadata, "imports"> {
  useFactory?: (
    ...args: any[]
  ) => IWeb3ModuleOptions | IWeb3ModuleOptions[] | Promise<IWeb3ModuleOptions> | Promise<IWeb3ModuleOptions[]>;
  inject?: any[];
}
