"use client";
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { LoaderCircle } from 'lucide-react';
import { db } from '@/utils/db';
import { MockInterview } from '@/utils/schema';
import { v4 as uuidv4 } from 'uuid';
import { useUser } from '@clerk/nextjs';
import moment from 'moment';
import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { chatSession } from '@/utils/GeminiAIModal';

function AddNewInterview() {
  const [openDialog, setOpenDialog] = useState(false);
  const [jobPosition, setJobPosition] = useState('');
  const [jobDesc, setJobDesc] = useState('');
  const [jobExperience, setJobExperience] = useState('');
  const [loading, setLoading] = useState(false);
  const [jsonResponse, setJsonResponse] = useState(null);
  const router = useRouter();
  const { user } = useUser();

  const onSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      console.log(jobPosition, jobDesc, jobExperience);

      const InputPrompt = `Job position: ${jobPosition}, Job Description: ${jobDesc}, Years of Experience: ${jobExperience}, Depends on Job Position, Job Description & Years of Experience give us ${process.env.NEXT_PUBLIC_INTERVIEW_QUESTION_COUNT} interview question along with answers in JSON format. Give us question and answer fields in JSON.`;

      const result = await chatSession.sendMessage(InputPrompt);
      const MockJsonResp = (await result.response.text()).replace('```json', '').replace('```', '');
      const parsedResponse = JSON.parse(MockJsonResp);

      console.log(parsedResponse);
      setJsonResponse(parsedResponse);

      if (parsedResponse) {
        const resp = await db.insert(MockInterview)
          .values({
            mockId: uuidv4(),
            jsonMockResp: MockJsonResp,
            jobPosition,
            jobDesc,
            jobExperience,
            createdBy: user?.primaryEmailAddress?.emailAddress,
            createdAt: moment().format('YYYY-MM-DD'), // Adjusted date format
          })
          .returning({ mockId: MockInterview.mockId });

        console.log("Inserted ID:", resp);

        if (resp) {
          setOpenDialog(false);
          router.push(`/dashboard/interview/${resp[0]?.mockId}`);
        }
      } else {
        console.error("Failed to generate AI response.");
      }
    } catch (error) {
      console.error("Error during AI generation or DB insert:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div 
        className='p-10 border rounded-lg bg-secondary hover:scale-105 hover:shadow-md cursor-pointer transition-all'
        onClick={() => setOpenDialog(true)}
      >
        <h2 className='text-lg text-center'>+ Add New</h2>
      </div>
      
      <Dialog open={openDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-2xl">Tell us more about your job interviewing</DialogTitle>
            <DialogDescription>
              <form onSubmit={onSubmit}>
                <h2>Add details about your job position/role, job description, and years of experience</h2>

                <div className='mt-7 my-3'>
                  <label>Job Role/Job Position</label>
                  <Input 
                    placeholder="Ex. Full Stack Developer" 
                    required 
                    value={jobPosition}
                    onChange={(event) => setJobPosition(event.target.value)} 
                  />
                </div>

                <div className='my-3'>
                  <label>Job Description/ Tech Stack (In Short)</label>
                  <Textarea 
                    placeholder="Ex. React, Angular, NodeJs, MySql etc" 
                    required 
                    value={jobDesc}
                    onChange={(event) => setJobDesc(event.target.value)} 
                  />
                </div>

                <div className='my-3'>
                  <label>Years of experience</label>
                  <Input 
                    placeholder="Ex. 5" 
                    type="number" 
                    max="50" 
                    required 
                    value={jobExperience}
                    onChange={(event) => setJobExperience(event.target.value)} 
                  />
                </div>

                <div className='flex gap-5 justify-end'>
                  <Button 
                    type="button" 
                    variant="ghost" 
                    onClick={() => setOpenDialog(false)}
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <LoaderCircle className='animate-spin' /> Generating from AI
                      </>
                    ) : (
                      'Start Interview'
                    )}
                  </Button>
                </div>
              </form>
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AddNewInterview;
