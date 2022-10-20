import { ApiProperty } from "@nestjs/swagger";
import { IValidatePasswordDto } from "../interfaces";
import { IsConfirm, IsPassword } from "../../common/validators";

export class ValidatePasswordDto implements IValidatePasswordDto {
  @ApiProperty()
  @IsPassword()
  public password: string;

  @ApiProperty()
  @IsConfirm()
  public confirm: string;
}
