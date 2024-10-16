const express = require('express');
const app = express();
const PORT = process.env.PORT || 3001;
const serverless =require('serverless-http')
const Alexa = require('ask-sdk-core');
const axios = require('axios'); 


const { IoTDataPlaneClient, PublishCommand } = require('@aws-sdk/client-iot-data-plane');
const iotClient = new IoTDataPlaneClient({ region: 'us-west-2' });
const sendIotCoreMsg = async (payload) => {
  console.log(payload);
  const publishCommand = new PublishCommand({
    topic: "pico",
    payload: JSON.stringify(payload),
    qos: 0
  });
  try {
    await iotClient.send(publishCommand);
  } catch (error) {
    console.error(error);
  }
}

// const AWS =require('aws-sdk');
// //const ddb = new AWS.DynamoDB.DocumentClient({region: 'eu-west-2'});
// var iotdata = new AWS.IotData({endpoint:"a17vu3qlg4e3g7-ats.iot.us-west-2.amazonaws.com"});
// const sendIotCoreMsg = async (payload) => {
//   const params = {
//     topic: 'pico',
//     payload: JSON.stringify(payload),
//     qos: 0
//   };
//   iotdata.publish(params, function(err, data){
//     if(err){
//       console.log("Error occured : ",err);
//     }
//   });
// }


const tableName = 'alexaresponse';
app.use(express.json());

if (process.env.ENVIRONMENT === 'lambda') {
  module.exports.handler = serverless(app);
} else {
  app.listen(PORT, () => {
    console.log(`Example app listening at http://localhost:${PORT}`);
  });
}

app.get('/', (req, res) => {
  console.log("connected");
  res.send({ status: "connected" });
});



const getresponse = async() => {
  const params = {
    TableName: tableName,
  Limit: 4001,
  };
  //console.log( ddb.scan(params).promise());
  // return ddb.scan(params).promise();
  return;
}

//**********update database**********
const updateDatabase = async (result, session, request, userId, deviceId) => {
  const params = {
    TableName: tableName,
    Key: { id: 1 }, // Ensure '1' is a valid id in your table
    UpdateExpression: 'set #result = :r, #dt = :d, #st = :s, #sess = :se, #req = :re, #uid = :ui, #did = :di',
    ExpressionAttributeValues: {
      ':r': result,
      ':d': new Date().toISOString()?.slice(11,19), // Use ISO string for better date handling
      ':s': "not done",
      ':se': session,
      ':re': request,
      ':ui': userId,
      ':di': deviceId,
    },
    ExpressionAttributeNames: {
      '#result': 'result', // Avoid using reserved words
      '#dt': 'datetime',
      '#st': 'status',
      '#sess': 'sessionId',
      '#req': 'RequestId',
      '#uid': 'userId',
      '#did': 'deviceId'
    }
  };

  //return ddb.update(params).promise();
  return;
};



const updateDatabase2 = async (result) => {
  const params = {
    TableName: tableName,
    Key: { id: 1 }, // Ensure '1' is a valid id in your table
    UpdateExpression: 'set #result = :r, #dt = :d',
    ExpressionAttributeValues: {
      ':r': result,
      ':d': new Date().toISOString()?.slice(11,19), // Use ISO string for better date handling
    },
    ExpressionAttributeNames: {
     '#result': 'result', // Avoid using reserved words
      '#dt': 'datetime',
    }
  };

  //return ddb.update(params).promise();
  return;
};

///**********Launch request**********
const LaunchRequestHandler = {
  canHandle(handlerInput) {
    return handlerInput.requestEnvelope.request.type === 'LaunchRequest';
  },
  async handle(handlerInput) {
    let shouldEndSession;
    // const result1 = await getresponse();
    // const alexastatus = result1?.Items[0]?.activity;
    const alexastatus = "active";
    console.log(alexastatus);
    let speechText
    if(alexastatus == "active"){
      speechText = 'Sure, what type of drink are you in the mood for?';
      shouldEndSession = false;
    }else{
      speechText = 'Sorry, It looks like your drink bot is offline';
      shouldEndSession = true;
    }
    const sessionId = handlerInput.requestEnvelope.session.sessionId;
    console.log(handlerInput.requestEnvelope);
    const deviceId = handlerInput.requestEnvelope.context.System.device.deviceId;
    const userId = handlerInput.requestEnvelope.context.System.user.userId;
    //console.log(deviceId, userId);
    console.log(sessionId, "session");

    const requestId = handlerInput.requestEnvelope.request.requestId;
    const result = {
      response: {
        outputSpeech: {
          type: 'PlainText',
          text: speechText
        },
        reprompt: {
          outputSpeech: {
            type: 'PlainText',
            text: speechText
          }
        },
        card: {
          type: 'Simple',
          title: 'Hello',
          content: speechText
        },
        shouldEndSession: false
      }
    };

    try {
      await updateDatabase(JSON.stringify(result), sessionId, requestId, userId, deviceId);
    } catch (error) {
      console.error('Database update failed:', error);
    }

    return handlerInput.responseBuilder
      .speak(speechText)
      .reprompt(speechText)
      .withSimpleCard('Hello', speechText)
      .withShouldEndSession(shouldEndSession)
      .getResponse();
  }
};


//**********Intent request **********
const TestIntentHandler =  {
  async  canHandle(handlerInput) {
      return handlerInput.requestEnvelope.request.type === 'IntentRequest' &&
        handlerInput.requestEnvelope.request.intent.name === 'test';
    },
    async handle(handlerInput) {
      const drink = handlerInput.requestEnvelope.request.intent.slots.drinks.value || '';
      console.log(drink);
      let speechText = '';
      let shouldEndSession = false;
      const sessionId = handlerInput.requestEnvelope.session.sessionId;
      // console.log(handlerInput.requestEnvelope);
      const requestId = handlerInput.requestEnvelope.request.requestId;
      const deviceId = handlerInput.requestEnvelope.context.System.device.deviceId;
      const userId = handlerInput.requestEnvelope.context.System.user.userId;
      try {
        // const response = await axios.get('https://5u0fw9o7ke.execute-api.eu-west-2.amazonaws.com/default/getdrinks');
        // const rawDrinks = response.data.drinks?.toLowerCase();
        // const validDrinks = rawDrinks.replace(/[\[\]"]/g, '').split(',').map(drink => drink.trim().split('.')[1].trim());
        const validDrinks = ["whiskey", "wine", "water", "merlot"];
        // const formattedDrinks = validDrinks.map((drink, index) => `${index + 1}.${drink}`).join(', ');
        const formattedDrinks = validDrinks.join(', ');
        const formattedDrinksString = `[${formattedDrinks}]`;
        console.log(formattedDrinksString);
      
        if (validDrinks.includes(drink) || validDrinks.includes(drink?.toLowerCase()) ) {
          /////**********if alexa get valid drink gives this response**********
          const res =   {"response":{"outputSpeech":{"type":"PlainText","text":"Sure, now pouring "+drink},"card":{"type":"Simple","title":drink,"content":"Sure, now pouring "+drink},"shouldEndSession":false}}
          await updateDatabase2(JSON.stringify(res));
          speechText = `Sure, now pouring ${drink} <break time="7s"/>Enjoy your ${drink},Can I pour you anything else`;
          shouldEndSession = false;
          const picoMsg = { intent: "pour", slots: { drink: drink }};
          console.log(picoMsg);
          await sendIotCoreMsg(picoMsg);
          // await new Promise(resolve => setTimeout(resolve, 8050));
          // const result = await getresponse();
          // const alexastatus = result?.Items[0]?.status;
          // console.log(result?.Items[0]?.status,result?.Items[0]?.status == "done",alexastatus.slice(1,5));
          // console.log(JSON.stringify(result?.Items[0]?.status) === "done" || result?.Items[0]?.status === "done" || alexastatus.slice(1,5) === "done")
          //         speechText = result?.Items[0]?.status === "done" || alexastatus.slice(1,5) === "done"?`Enjoy your ${drink},Can I pour you anything else`:`Enjoy`;
          //   handlerInput.responseBuilder
          //   .speak(speechText)
          //  .withSimpleCard(drink, speechText)
          //  .withShouldEndSession(shouldEndSession)
          // .getResponse();
          //   console.log(speechText)
          // shouldEndSession = result?.Items[0]?.status === "done" || alexastatus.slice(1,5) === "done"?false:true; 
        } else if(drink == "yes"){
          //**********if alexa get yes from user side gives this response**********
          speechText = `Sure, what type of drink are you in the mood for?`;
          shouldEndSession = false;
        } else if(drink == "no" || drink == "No"){
          //**********if alexa get no from user side gives this response**********
          speechText = `Enjoy`;
          shouldEndSession = true;
        } else {
           //**********if alexa get invalid drink from user side gives this response**********
          speechText = `Sorry, Please choose any one of the following: ${formattedDrinksString}, \n
          Would you like one of these drinks?`;
          shouldEndSession = false; // Keep session open if drink is not valid
        }
        
        
        /////**********result saved in database**********
        const result = {
          // sessionId: sessionId,
       // requestId: requestId,
          response: {
            outputSpeech: {
              type: 'PlainText',
              text: speechText
            },
            card: {
              type: 'Simple',
              title: drink,
              content: speechText
            },
            shouldEndSession: shouldEndSession
          }
        };
        
        ///********** update query to update result**********
        await updateDatabase(JSON.stringify(result),sessionId,requestId,userId,deviceId);
      } catch (error) {
        console.error('API call or Database update failed:', error);
        speechText = 'There was an error processing your request. Please try again later.';
        shouldEndSession = false;
      }
      return handlerInput.responseBuilder
        .speak(speechText)
        .withSimpleCard(drink, speechText)
        .withShouldEndSession(shouldEndSession)
        .getResponse();
    }
  };

//**********help intent
const HelpIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest' &&
      Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.HelpIntent';
  },
  handle(handlerInput) {
    const speakOutput = 'You can say hello to me! How can I help?';

    return handlerInput.responseBuilder
      .speak(speakOutput)
      .reprompt(speakOutput)
      .getResponse();
  }
};


const NoIntentHandler = {
  canHandle(handlerInput) {
    return handlerInput.requestEnvelope.request.type === 'IntentRequest' &&
      handlerInput.requestEnvelope.request.intent.name === 'AMAZON.NoIntent';
  },
  handle(handlerInput) {
    const speechText = 'Enjoy';

    return handlerInput.responseBuilder
      .speak(speechText)
      .withSimpleCard('Drink Bot', speechText)
      .withShouldEndSession(true)
      .getResponse();
  }
};

const CancelAndStopIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest' &&
      (Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.CancelIntent' ||
        Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.StopIntent');
  },
  handle(handlerInput) {
    const speakOutput = 'Goodbye!';

    return handlerInput.responseBuilder
      .speak(speakOutput)
      .getResponse();
  }
};

const FallbackIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest' &&
      Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.FallbackIntent';
  },
  handle(handlerInput) {
    const speakOutput = 'Sorry, I don\'t know about that. Please try again.';

    return handlerInput.responseBuilder
      .speak(speakOutput)
      .reprompt(speakOutput)
      .getResponse();
  }
};

const SessionEndedRequestHandler = {
  canHandle(handlerInput) { 
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'SessionEndedRequest';
  },
  handle(handlerInput) {
    console.log(`~~~~ Session ended: ${JSON.stringify(handlerInput.requestEnvelope)}`);
    return handlerInput.responseBuilder.getResponse();
  }
};

const IntentReflectorHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest';
  },
  handle(handlerInput) {
    const intentName = Alexa.getIntentName(handlerInput.requestEnvelope);
    const speakOutput = `You just triggered ${intentName}`;

    return handlerInput.responseBuilder
      .speak(speakOutput)
      .getResponse();
  }
};

const ErrorHandler = {
  canHandle() {
    return true;
  },
  handle(handlerInput, error) {
    const speakOutput = 'Sorry, I had trouble doing what you asked. Please try again.';
    console.log(`~~~~ Error handled: ${JSON.stringify(error)}`);

    return handlerInput.responseBuilder
      .speak(speakOutput)
      .reprompt(speakOutput)
      .getResponse();
  }
};

exports.handler = Alexa.SkillBuilders.custom()
  .addRequestHandlers(
    LaunchRequestHandler,
    TestIntentHandler,
    HelpIntentHandler,
    NoIntentHandler,
    CancelAndStopIntentHandler,
    FallbackIntentHandler,
    SessionEndedRequestHandler,
    IntentReflectorHandler
  )
  .addErrorHandlers(ErrorHandler)
  .lambda();
