Next Steps:

1. Merge JobSpy code to gather jobs from the big job boards.

1. Create script to update database with new jobs.  This will be run as a cron job independently of the API or web interfaces

1. Create cron job to scan sites periodically
    - probably at least twice a day - 12:00 noonish, and midnight-ish perhaps.

1. Create User table / system

1. Create REST Interface

    - Authentication
    - User Dashboard
    - Stripe Webhooks

1. Create Front End

    - Home page
    - Signup
    - Login
    - Forgot Password
    - Public Keyword Comparison
        - user cuts/pastes their resume content 
            - store resume keywords to LocalStorage
        - user cuts/pastes a job posting/description
        - keyword comparison is done to score the match
    - Authenticated User Dashboard
        - Allow user to upload one or more resumes.  Maximum of 3.
        - Shows best matches overall, and per resume.

1. Add Email feature

    - paid subscriptions can receive daily/weekly/monthly emails listing the 10 best matches at that time, instead of having to log in every day.

1. Expand sites.

    - Add more career pages
    - perhaps sites can be matched to a geographical location (i.e. "Calgary Area", "Alberta", "Ontario", "Canada", etc.
    

...

11. Promote the Saas
12. Profit... ????


