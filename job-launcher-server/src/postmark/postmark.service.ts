import { Inject, Injectable, Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { Models, ServerClient } from "postmark";
import { v4 } from "uuid";

import { ProviderType } from "../common/constants/providers";
import { UserEntity } from "../user/user.entity";
import { TokenEntity } from "../token/token.entity";

@Injectable()
export class PostmarkService {
  private readonly logger = new Logger(PostmarkService.name);

  constructor(
    @Inject(ProviderType.POSTMARK)
    private readonly client: ServerClient,
    private readonly configService: ConfigService,
  ) {}

  public sendEmailVerification(userEntity: UserEntity, token: TokenEntity): Promise<Record<string, any>> {
    return this.sendEmailWithTemplate(userEntity.email, "email_verify", {
      name: userEntity.email,
      url: `/activation?token=${token.uuid}`,
    });
  }

  public sendForgotPassword(userEntity: UserEntity, token: TokenEntity): Promise<Record<string, any>> {
    return this.sendEmailWithTemplate(userEntity.email, "forgot_pass", {
      name: userEntity.email,
      url: `/restore-password?token=${token.uuid}`,
    });
  }

  public sendRestorePassword(userEntity: UserEntity): Promise<Record<string, any>> {
    return this.sendEmailWithTemplate(userEntity.email, "restore_pass", {
      name: userEntity.email,
    });
  }

  private sendEmailWithTemplate(
    email: string,
    template: string,
    model: Record<string, string | number>,
  ): Promise<Models.MessageSendingResponse> {
    const nodeEnv = this.configService.get<string>("NODE_ENV");

    if (nodeEnv === "test") {
      return Promise.resolve({
        SubmittedAt: new Date().toISOString(),
        MessageID: v4(),
        ErrorCode: 0,
        Message: "Message",
      });
    }

    this.logger.log(`Sending ${template} to user ${model.userId}`);

    const from = this.configService.get<string>("EMAIL_FROM", "");
    const feUrl = this.configService.get<string>("FE_URL", "");

    model.url = `${feUrl}${model.url}`;

    return this.client
      .sendEmailWithTemplate({
        From: from,
        To: email,
        TemplateAlias: template,
        TemplateModel: model,
        Tag: template,
      })
      .catch(e => {
        this.logger.error(e.message, e.stack, PostmarkService.name);
        return {
          SubmittedAt: new Date().toISOString(),
          MessageID: v4(),
          ErrorCode: 100500,
          Message: e.message,
        };
      });
  }
}
