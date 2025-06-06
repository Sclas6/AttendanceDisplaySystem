import React from "react";
import axios from "axios";
//import { format } from "https://cdn.jsdelivr.net/gh/ymd-h/format-js/format.js";
import { format } from "./format.js";
import { useKey } from "rooks";
import ModalComponent from "./ModalComponent";
import Modal from 'react-modal';

let MODE_EXIST = 0
let MODE_ORDER = 1

function App() {
  //useKey('a', console.log("q"));
  const [data, setData] = React.useState();
  const [url_graph, setUrl] = React.useState();
  const [mode_sort, setMode] = React.useState(MODE_ORDER)
  const [isError, setIsError] = React.useState(false);
  const url = "http://172.16.15.7:8000"

  const sortData = (data, mode) => {
    var newData = { "content": [] }
    if (mode === MODE_EXIST) {
      //console.log("a")
      var existUsers = { "content": [] }
      var afkUsers = { "content": [] }
      var inexistUsers = { "content": [] }
      for (const user of data.content) {
        if ((user.status === "clock_in") || (user.status === "break_out")) {
          existUsers.content.push(user)
        }
      }
      for (const user of data.content) {
        if (user.status === "break_in") {
          afkUsers.content.push(user)
        }
      }
      for (const user of data.content) {
        if (user.status === "clock_out") {
          inexistUsers.content.push(user)
        }
      }
      existUsers = sortData(existUsers, MODE_ORDER)
      afkUsers = sortData(afkUsers, MODE_ORDER)
      inexistUsers = sortData(inexistUsers, MODE_ORDER)
      for (const user of existUsers.content) newData.content.push(user)
      for (const user of afkUsers.content) newData.content.push(user)
      for (const user of inexistUsers.content) newData.content.push(user)

    } else if (mode === MODE_ORDER) {
      for (const user of data.content) {
        if (user.grade === "D") {
          newData.content.push(user)
        }
      }
      for (const user of data.content) {
        if (user.grade === "M2") {
          newData.content.push(user)
        }
      }
      for (const user of data.content) {
        if (user.grade === "M1") {
          newData.content.push(user)
        }
      }
      for (const user of data.content) {
        if (user.grade === "B4") {
          newData.content.push(user)
        }
      }
      for (const user of data.content) {
        if (user.grade === "B3") {
          newData.content.push(user)
        }
      }
      for (const user of data.content) {
        if (user.grade === "UNKNOWN") {
          newData.content.push(user)
        }
      }
    }
    else {
      newData = data
    }
    return newData
  };

  const GetData = async (mode) => {
    try {
      const res = await axios.get(url)
      setData(sortData(res.data, mode));
      setIsError(false);
    } catch (error) {
      setIsError(true);
      console.log(error)
    }
  };

  const getMode = () => {
    return mode_sort
  };

  const Update_Graph_2 = (name) => {
    try {
      axios.get(format("http://172.16.15.7:8000/update/{0}", name)).then((res) => {
        setUrl(res.data.url)
      });
      setIsError(false);
    } catch (error) {
      setIsError(true);
      console.log(error)
    }
  };

  const Update_Graph = async (data) => {
    try {
      let users = {}
      data.content.map((user, i) => {
        axios.get(format("http://172.16.15.7:8000/update/{0}", user.name)).then((res) => {
          const url_g = res.data.url
          users[user.name] = url_g
        });
        setIsError(false);
        return users
      })
    } catch (error) {
      setIsError(true);
      console.log(error)
    }
  };

  const [modalOpen, setModalOpen] = React.useState([]);

  const handleOpenModal = (index) => {
    const newModalOpen = [...modalOpen];
    newModalOpen[index] = true;
    setModalOpen(newModalOpen);
  };

  const handleCloseModal = (index) => {
    const newModalOpen = [...modalOpen];
    newModalOpen[index] = false;
    setModalOpen(newModalOpen);
  };

  React.useEffect(() => {
    async function fetchData() {
      GetData(getMode())
    }
    const interval = setInterval(() => {
      fetchData();
    }, 2000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode_sort]);

  React.useEffect(() => {
    async function fetchData() {
      window.location.reload()
    }
    const interval = setInterval(() => {
      fetchData()
    }, 1800000)
    return () => clearInterval(interval)
  }, []) 

  const handleKewDownEnter = () => {
    switch (getMode()) {
      case 0:
        setMode(1)
        GetData(1)
        break
      case 1:
        setMode(0)
        GetData(0)
        break
      default:
        break
    }
  };
  useKey(["a"], handleKewDownEnter)
  Modal.setAppElement("#root")
  return (
    <>
      <div className="menu">
        {<button
          onClick={() => {
            GetData(getMode())
            console.log(isError)
            if (!isError) {
              data ? Update_Graph(data) : console.log("Log", "No Checks")
            }
          }}
          className="button_out_table">手動更新</button>}
      </div>
      <table className="table">
        <thead>
          <tr>
            <th scope="col">名前</th>
            <th scope="col">在室</th>
            <th scope="col">一時不在</th>
            <th scope="col">帰宅</th>
          </tr>
        </thead>
        {data ? data.content.map((user, i) => {
          return <tbody key={user.name} className={format("grade_{0}", user.grade)}>
            <tr height={format("{0}vh", parseInt(800 / (data.content.length)))}>
              <th scope="row">
                <a className="name" onClick={() => {
                  handleOpenModal(i);
                  Update_Graph_2(user.name)
                }}>{user.name.length < 10 ? user.name.replace(" ", "　") : user.name.substring(0, 6)}</a>
                <ModalComponent
                  isOpen={modalOpen[i]}
                  title={user.name}
                  name={user.name}
                  url={url_graph}
                  onClose={() => handleCloseModal(i)}
                />
              </th>
              <td>{((user.status === "clock_in") || (user.status === "break_out")) ? <div className="border-radius-1"></div> : ""}</td>
              <td>{user.status === "break_in" ? <div className="border-radius-2"></div> : ""}</td>
              <td>{user.status === "clock_out" ? <div className="border-radius-3"></div> : ""}</td>
            </tr>
          </tbody>
        }) :
          <tbody></tbody>}
      </table>
      <div className="sortButton">
        <button className={mode_sort === 0 ? "active" : "deactive"} onClick={() => {
          setMode(0);
          GetData(0)
        }}>在室順</button>
        <button className={mode_sort === 1 ? "active" : "deactive"} onClick={() => {
          setMode(1)
          GetData(1)
        }}>学年順</button>
      </div>
      {/*<h2 className="foot">名前タップでclock_in時間表示</h2>*/}
    </ >
  );
}

export default App;