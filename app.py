import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import pandas as pd

st.set_page_config(layout="wide")

st.sidebar.title("Whatsapp Chat Analyzer")

uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")
    df = preprocessor.preprocess(data)

    st.dataframe(df)

    # to fetch individual users
    user_list = df['user'].unique().tolist()
    user_list.remove('group_notification')
    user_list.sort()
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("Show analysis ", user_list)

    if st.sidebar.button("Show Analysis"):

        # for stats area
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        st.title("Top Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label="Total Messages", value=num_messages)
        with col2:
            st.metric(label="Total Words", value=words)
        with col3:
            st.metric(label="Media Shared", value=num_media_messages)
        with col4:
            st.metric(label="Links Shared", value=num_links)

        # download csv
        csv_data = pd.DataFrame({
            "Metric": ["Total Messages", "Total Words", "Media Shared", "Links Shared"],
            "Count": [num_messages, words, num_media_messages, num_links]
        })

        csv = csv_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Report as CSV",
            data=csv,
            file_name='whatsapp_report.csv',
            mime='text/csv'
        )

        # monthly timeline
        st.title("Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['message'], color='green')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # daily timeline
        st.title("Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # activity map
        st.title('Activity Map')
        col1, col2 = st.columns(2)

        with col1:
            st.header("Most busy day")
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='purple')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        with col2:
            st.header("Most busy month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        # Heatmap
        st.title("Weekly Activity Map")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        fig, ax = plt.subplots()
        ax = sns.heatmap(user_heatmap)
        st.pyplot(fig)

        # finding the busiest users in the group(Group level)
        if selected_user == 'Overall':
            st.title('Most Busy Users')
            x, new_df = helper.most_busy_users(df)
            fig, ax = plt.subplots()

            col1, col2 = st.columns(2)

            with col1:
                ax.bar(x.index, x.values, color='red')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            with col2:
                st.dataframe(new_df)

        # Wordcloud
        st.title("Wordcloud")
        df_wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots()
        ax.imshow(df_wc)
        st.pyplot(fig)

        # most common words
        most_common_df = helper.most_common_words(selected_user, df)

        fig, ax = plt.subplots()

        ax.barh(most_common_df[0], most_common_df[1])
        plt.xticks(rotation='vertical')

        st.title('Most common words')
        st.pyplot(fig)

        # Emoji Analysis
        emoji_df = helper.emoji_helper(selected_user, df)
        st.title("Emoji Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(emoji_df)
        with col2:
            import matplotlib.pyplot as plt
            plt.rcParams['font.family'] = 'DejaVu Sans'
            fig, ax = plt.subplots()
            ax.pie(emoji_df[1].head(), labels=emoji_df[0].head(), autopct="%.2f")
            st.pyplot(fig)

    # Compare two users
    if len(user_list) > 2:
        st.sidebar.title("Compare Two Users")
        user1 = st.sidebar.selectbox("Select first user", user_list, key="user1")
        user2 = st.sidebar.selectbox("Select second user", user_list, key="user2")

        if st.sidebar.button("Compare"):
            st.title(f"Comparison between {user1} and {user2}")

            metrics = []
            for user in [user1, user2]:
                user_df = df[df['user'] == user]
                num_messages = user_df.shape[0]
                word_count = user_df['message'].apply(lambda x: len(x.split())).mean()
                media_shared = user_df[user_df['message'] == '<Media omitted>\n'].shape[0]
                emoji_count = sum(user_df['message'].apply(lambda msg: sum(c in helper.emoji.UNICODE_EMOJI['en'] for c in msg)))

                metrics.append({
                    "User": user,
                    "Message Count": num_messages,
                    "Average Words": round(word_count, 2),
                    "Media Shared": media_shared,
                    "Emoji Count": emoji_count
                })

            st.dataframe(pd.DataFrame(metrics))
