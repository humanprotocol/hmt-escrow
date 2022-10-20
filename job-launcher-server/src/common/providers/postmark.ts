import { ConfigModule, ConfigService } from "@nestjs/config";
import { ServerClient } from "postmark";
import { ProviderType } from "../constants/providers";

export const postmarkProvider = {
  provide: ProviderType.POSTMARK,
  inject: [ConfigService],
  import: [ConfigModule],
  useFactory: (configService: ConfigService): ServerClient => {
    const apiKey = configService.get<string>("POSTMARK_API_KEY", "");
    return new ServerClient(apiKey);
  },
};
