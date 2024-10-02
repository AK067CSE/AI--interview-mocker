/** @type { import("drizzle-kit").Config } */
export default {
    schema: "./utils/schema.js",
    dialect: 'postgresql',
    dbCredentials: {
      url:'postgresql://AI-Interview-Mocker_owner:b1TCRIu0SMvz@ep-orange-star-a53ncwxq.us-east-2.aws.neon.tech/AI-Interview-Mocker?sslmode=require' ,
    }
  };