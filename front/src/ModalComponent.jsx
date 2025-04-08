import React from 'react';
import Modal from 'react-modal';

class ModalComponent extends React.Component {
    constructor(props) {
        super(props);

        this.handleCloseModal = this.handleCloseModal.bind(this);
    }

    handleCloseModal() {
        this.props.onClose();
    }

    render() {
        return (
            <Modal isOpen={this.props.isOpen} contentLabel="Example Modal" className="Modal">
                <br></br>
                <button className='TextinModal'>{this.props.title}</button>
                <img src={this.props.url} alt="graph" className='graph' />
                <br></br>
                <button onClick={this.handleCloseModal} className='ButtoninModal'>閉じる</button>
            </Modal>
        );
    }
}

export default ModalComponent;