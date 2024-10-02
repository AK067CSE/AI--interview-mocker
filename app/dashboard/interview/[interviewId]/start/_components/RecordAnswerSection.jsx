"use client";
import Webcam from 'react-webcam';
import React, { useEffect, useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import useSpeechToText from 'react-hook-speech-to-text';
import { Mic } from 'lucide-react';
import { toast } from 'sonner';
import { chatSession } from '@/utils/GeminiAIModal';
import { db } from '@/utils/db';
import { UserAnswer } from '@/utils/schema';
import { useUser } from '@clerk/nextjs';
import moment from 'moment';

function RecordAnswerSection({ mockInterviewQuestion, activeQuestionIndex, interviewData }) {
  const [userAnswer, setUserAnswer] = useState('');
  const { user } = useUser();
  const [loading, setLoading] = useState(false);

  const {
    error,
    interimResult,
    isRecording,
    results,
    startSpeechToText,
    stopSpeechToText,
    setResults
  } = useSpeechToText({
    continuous: true,
    useLegacyResults: false,
  });

  // Append each transcript result to the userAnswer state
  useEffect(() => {
    results.forEach((result) => {
      setUserAnswer((prevAns) => prevAns + result.transcript);
    });
  }, [results]);

  // Auto-update the answer when recording stops and answer length is >10 characters
  useEffect(() => {
    if (!isRecording && userAnswer.length > 10) {
      UpdateUserAnswer();
    }
  }, [userAnswer]);

  // Function to start or stop recording
  const StartStopRecording = async () => {
    if (isRecording) {
      stopSpeechToText();
    } else {
      startSpeechToText();
    }
  };

  // Function to update and store the user answer in the database
  const UpdateUserAnswer = async () => {
    try {
      setLoading(true);

      const feedbackPrompt =
        "Question: " + mockInterviewQuestion[activeQuestionIndex]?.question +
        ", UserAnswer: " + userAnswer +
        ", Depends on the question and user answer for the given interview question, " +
        "please provide a rating and feedback as an area for improvement, " +
        "in 3 to 5 lines, in JSON format with rating and feedback fields.";

      const result = await chatSession.sendMessage(feedbackPrompt);
      const mockJsonResp = (await result.response.text())
        .replace('```json', '')
        .replace('```', '');

      const JsonFeedbackResp = JSON.parse(mockJsonResp);

      // Log feedback and rating to the console
      console.log("Feedback:", JsonFeedbackResp?.feedback);
      console.log("Rating:", JsonFeedbackResp?.rating);

      // Ensure interviewData has the required mockId
      if (!interviewData?.mockId) {
        toast.error('Mock interview ID is missing. Cannot record answer.');
        setLoading(false);
        return;
      }

      // Insert user's answer into the database
      const resp = await db.insert(UserAnswer).values({
        mockIdRef: interviewData?.mockId,
        question: mockInterviewQuestion[activeQuestionIndex]?.question,
        correctAns: mockInterviewQuestion[activeQuestionIndex]?.answer,
        userAns: userAnswer,
        feedback: JsonFeedbackResp?.feedback,
        rating: JsonFeedbackResp?.rating,
        userEmail: user?.primaryEmailAddress?.emailAddress,
        createdAt: moment().format('DD-MM-YYYY'), // Format the creation date properly
      });

      if (resp) {
        toast.success('User answer recorded successfully');
      }

      setUserAnswer('');
      setResults([]);
    } catch (error) {
      console.error("Error updating user answer:", error);
      toast.error('An error occurred while recording the answer.');
    } finally {
      setResults([]);
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center flex-col">
      <div className="flex flex-col mt-20 justify-center items-center bg-black rounded-lg p-5">
        <Image src={'/webcam.png'} width={200} height={200} className="absolute" />
        <Webcam
          mirrored={true}
          style={{
            height: 300,
            width: '100%',
            zIndex: 10,
          }}
        />
      </div>

      <Button
        disabled={loading}
        variant="outline"
        className="my-10"
        onClick={StartStopRecording}
      >
        {isRecording ? (
          <h2 className="text-red-600 flex gap-2">
            <Mic /> Stop Recording
          </h2>
        ) : (
          'Record Answer'
        )}
      </Button>

      <Button onClick={() => console.log(userAnswer)}>Show User Answer</Button>
    </div>
  );
}

export default RecordAnswerSection;
