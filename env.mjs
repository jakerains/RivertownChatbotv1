import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    AWS_REGION: z.string(),
    AWS_ACCESS_KEY_ID: z.string(),
    AWS_SECRET_ACCESS_KEY: z.string(),
    BEDROCK_KB_ID: z.string(),
    BLAND_API_KEY: z.string(),
    CUSTOMER_SERVICE_PHONE: z.string(),
  },
  client: {
    // Add any client-side env vars here if needed
  },
  runtimeEnv: {
    AWS_REGION: process.env.AWS_REGION,
    AWS_ACCESS_KEY_ID: process.env.AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY: process.env.AWS_SECRET_ACCESS_KEY,
    BEDROCK_KB_ID: process.env.BEDROCK_KB_ID,
    BLAND_API_KEY: process.env.BLAND_API_KEY,
    CUSTOMER_SERVICE_PHONE: process.env.CUSTOMER_SERVICE_PHONE,
  },
}); 