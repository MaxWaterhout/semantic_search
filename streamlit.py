import streamlit as st
import torch
from sentence_transformers import SentenceTransformer,util
import pandas as pd
import re 

@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_data
def load_df():
    return pd.read_pickle('df_semantic_search.pkl')

class SemanticSearch:
    def __init__(self):
        self.df_embeddings = None
        self.model_semantic_search = None
        self.threshold = None
        self.question_embedding = None
        self.top_scores = None
        self.n_videos = None

    def main(self):
        self.df_embeddings = load_df()
        self.model_semantic_search = load_model()
        st.title("Semantic searching")

        # Ask the user for their question
        question = st.text_input("Input for searching:")
        self.threshold = st.sidebar.slider("Threshold:", min_value=0.0, max_value=1.0, step=0.01, value=0.6)
        self.n_videos = st.sidebar.select_slider("Select how many videos to show", options=[1, 2, 3, 4, 5])

        # Display a button to submit the question
        if st.button("Submit"):
            # Process the question and get the answer
            if question == '':
                st.subheader("Please fill the input!")
            else:
                self.question_embedding = self.embed_question(question)
                # Display the answer
                self.top_scores = self.search_top_results(self.question_embedding)
                if len(self.top_scores) == 0:
                    st.subheader("Confidence is too low for the search")
                else:
                    self.display_top_result(self.top_scores)

    def embed_question(self,question):
        question_embedding = self.model_semantic_search.encode(question)
        return question_embedding
    
    st.cache_data()
    def search_top_results(self,query_embedding):
        cos_scores = util.cos_sim(query_embedding, self.df_embeddings['passage_embedding'])[0]
        top_results = torch.topk(cos_scores, k=self.n_videos)
        # Get the values and indices from top_results
        values = top_results.values
        indices = top_results.indices
        # Filter scores based on the threshold and create a dictionary
        filtered_scores = {index.item(): value.item() for value, index in zip(values, indices) if value >= self.threshold}
        return filtered_scores
    
    def display_top_result(self,top_results):
        keys = list(top_results.keys())
        for i in range(len(keys)):
            top_result_row = self.df_embeddings.iloc[int(keys[i])]
            video_id = top_result_row['video_id'] 
            #grouped_text = self.df_embeddings.loc[self.df_embeddings['video_id'] == video_id]['text']

            st.subheader(f"From **{self.seconds_to_minutes(top_result_row['start_time'])}** :")# Example usage

            top_result_row_plus1 = self.df_embeddings.iloc[int(keys[i])+1]
            top_result_row_plus2 = self.df_embeddings.iloc[int(keys[i])+2]
            top_result_row_min1 = self.df_embeddings.iloc[int(keys[i])-1]
            top_result_row_min2 = self.df_embeddings.iloc[int(keys[i])-2]
            all_text = ' '.join([top_result_row_min2['text'],top_result_row_min1['text'],top_result_row['text'],top_result_row_plus1['text'],top_result_row_plus2['text']])
            all_text = self.strip_sentence(all_text)
            text = top_result_row['text'].strip()

            #all_text = ' '.join(grouped_text)
            col1, col2 = st.columns([1.75, 1])  # Adjust the widths as needed

            pretty_stack = re.sub(rf"({re.escape(text)})", r"**\1**", all_text, flags=re.IGNORECASE)
            with col1:
                st.video(f'https://www.youtube.com/watch?v={video_id}',start_time=top_result_row['start_time'])
            with col2:
                st.markdown(pretty_stack, unsafe_allow_html=True)

    def strip_sentence(self, sentence, max_words=80):
        # Split the sentence into words
        words = sentence.split()
        # If the number of words exceeds the maximum, trim it
        if len(words) > max_words:
            n_words_to_trim = int((len(words) - max_words)/2)            
            # Trim the sentence, keeping the middle part unchanged
            stripped_words = words[:len(words) -n_words_to_trim][n_words_to_trim:]

            # Join the words back into a sentence
            stripped_sentence = ' '.join(stripped_words)
        else:
            stripped_sentence = sentence
        
        return stripped_sentence

    def seconds_to_minutes(self,seconds):
        # Calculate minutes and remaining seconds
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes}:{seconds:02d}"  # Format output as "minutes:seconds"


    

if __name__ == "__main__":
    app = SemanticSearch()
    app.main()