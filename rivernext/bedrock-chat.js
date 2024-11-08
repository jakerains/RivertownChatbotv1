require('dotenv').config({ path: '.env.local' });
const axios = require('axios');

const bedrockChat = async () => {
    try {
        const response = await axios.post(
            `https://bedrock.${process.env.AWS_REGION}.amazonaws.com/model/us.anthropic.claude-3-5-haiku-20241022-v1:0/invoke`,
            {
                contentType: "application/json",
                accept: "application/json",
                body: JSON.stringify({
                    anthropic_version: "bedrock-2023-05-31",
                    max_tokens: 200,
                    messages: [
                        {
                            role: "user",
                            content: [
                                {
                                    type: "text",
                                    text: "hello world"
                                }
                            ]
                        }
                    ]
                })
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `AWS4-HMAC-SHA256 Credential=${process.env.AWS_ACCESS_KEY_ID}`,
                    'Accept': 'application/json',
                    'X-Amz-Content-Sha256': 'UNSIGNED-PAYLOAD',
                    'X-Amz-Date': new Date().toISOString().replace(/[:-]|\.\d{3}/g, '')
                }
            }
        );
        console.log('Response:', response.data);
    } catch (error) {
        console.error('Error:', error.response ? error.response.data : error.message);
    }
};

module.exports = bedrockChat;
