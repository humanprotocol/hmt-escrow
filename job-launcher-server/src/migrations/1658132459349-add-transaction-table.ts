import { MigrationInterface, QueryRunner, Table } from "typeorm";
import { NS } from "../common/constants";

export class addTransactionTable1658132459349 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<any> {
    await queryRunner.query(`
      CREATE TYPE ${NS}.transaction_type_enum AS ENUM (
        'TOPUP',
        'ESCROW_CREATE',
        'ESCROW_SETUP'
      );
    `);

    await queryRunner.query(`
      CREATE TYPE ${NS}.transaction_status_enum AS ENUM (
        'PENDING',
        'CONFIRMED'
      );
    `);

    const table = new Table({
      name: `${NS}.transaction`,
      columns: [
        {
          name: "id",
          type: "serial",
          isPrimary: true,
        },
        {
          name: "job_id",
          type: "int",
          isNullable: true,
        },
        {
          name: "amount",
          type: "decimal",
          isNullable: true,
        },
        {
          name: "hash",
          type: "varchar",
        },
        {
          name: "confirmations",
          type: "int",
          default: 0,
        },
        {
          name: "type",
          type: `${NS}.transaction_type_enum`,
        },
        {
          name: "status",
          type: `${NS}.transaction_status_enum`,
        },
        {
          name: "created_at",
          type: "timestamptz",
        },
        {
          name: "updated_at",
          type: "timestamptz",
        },
      ],
      foreignKeys: [
        {
          columnNames: ["job_id"],
          referencedColumnNames: ["id"],
          referencedTableName: `${NS}.job`,
          onDelete: "CASCADE",
        },
      ],
    });

    await queryRunner.createTable(table, true);
  }

  public async down(queryRunner: QueryRunner): Promise<any> {
    await queryRunner.dropTable(`${NS}.transaction`);
    await queryRunner.query(`DROP TYPE ${NS}.transaction_type_enum;`);
    await queryRunner.query(`DROP TYPE ${NS}.transactionstatus_enum;`);
  }
}
