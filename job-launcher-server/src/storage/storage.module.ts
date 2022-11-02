import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";

import { StorageService } from "./storage.service";
import { s3Provider } from "../common/providers";
import { S3 } from "aws-sdk";

@Module({
  imports: [ConfigModule],
  providers: [s3Provider, StorageService],
  exports: [StorageService],
})
export class StorageModule {}
